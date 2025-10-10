import datetime
import logging
from enum import IntEnum

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import models
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import AbstractApplication
from simple_history.models import HistoricalRecords

from members.models import Tag, User

logger = logging.getLogger(__name__)

# We log unknown tags; to make adding them from a
# recently seen list easy. But we do not want the
# table to grow endlessly. So these are some hard
# caps put on it.
#
MAX_USERS_TRACKED = 5
DAYS_USERS_TRACKED = 3


class MachineUseFlags(IntEnum):
    ACTIVE = 1
    PERMIT = 2
    FORM = 4
    APPROVE = 8
    INSTRUCT = 16
    BUDGET = 32
    OVERRIDE = 64


def bits2str(needs, has):
    if needs:
        if has:
            return "yes"
        else:
            return "fail"
    else:
        if has:
            return "NN"
    return "n/a"


def useNeedsToStateStr(needs, has):
    out = "user:" + bits2str(
        needs & MachineUseFlags.ACTIVE, has & MachineUseFlags.ACTIVE
    )
    out += ", permit:" + bits2str(
        needs & MachineUseFlags.PERMIT, has & MachineUseFlags.PERMIT
    )
    out += ", waiver:" + bits2str(
        needs & MachineUseFlags.FORM, has & MachineUseFlags.FORM
    )
    out += ", approve:" + bits2str(
        needs & MachineUseFlags.APPROVE, has & MachineUseFlags.APPROVE
    )

    if has & MachineUseFlags.INSTRUCT:
        out += ", instructor=yes"
    else:
        out += ", instructor=no"
    if has & MachineUseFlags.BUDGET:
        out += ", budget=sufficient"
    else:
        out += ", budget=no"
    if needs & MachineUseFlags.OVERRIDE:
        out += ", override: "
        if has & MachineUseFlags.OVERRIDE:
            out += "yes (and needed, machine locked)"
        else:
            out += "machine is locked out"
    else:
        out += ", override:" + bits2str(
            needs & MachineUseFlags.OVERRIDE, has & MachineUseFlags.OVERRIDE
        )
    out += " = "
    if has & needs == needs:
        out += "ok"
    else:
        out += "denied"
    return out


class PermitType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200)
    require_ok_trustee = models.BooleanField(
        default=False,
        verbose_name="Requires explicit trustee OK",
        help_text="i.e. the trustees need to also explictly approve it when the permit is granted.",
    )
    permit = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Permit reqiured",
        help_text='i.e. permit required by the issuer (default is none needed)"',
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def hasThisPermit(self, user):
        e = Entitlement.objects.all().filter(holder=user, permit=self).first()
        if e and e.active is True:
            return True
        return False

    class Meta:
        ordering = ["name"]


class Location(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class NodeField(models.CharField):
    def get_prep_value(self, value):
        return str(value).lower()


class Machine(models.Model):
    name = models.CharField(max_length=40, unique=True)

    node_name = NodeField(
        max_length=20, blank=True, help_text="Name of the controlling node"
    )
    node_machine_name = NodeField(
        max_length=20,
        blank=True,
        help_text="Name of device or machine used by the node",
    )

    description = models.CharField(max_length=200, blank=True)
    location = models.ForeignKey(
        Location,
        related_name="is_located",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    requires_instruction = models.BooleanField(default=False)
    requires_form = models.BooleanField(default=False)
    requires_permit = models.ForeignKey(
        PermitType,
        related_name="has_permit",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    out_of_order = models.BooleanField(default=False)
    do_not_show = models.BooleanField(
        default=False,
        help_text="Do not show this machine in CRM browse/listings (but it will be in API and other automatic lists). Useful for test machines or machines that are a hidden node of a larger machine",
    )

    CATEGORY_CHOICES = [
        ("machine", "Machine"),
        ("general_equipment", "General equipment"),
        ("software", "Software"),
        ("lights", "Lights"),
    ]

    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="machine"
    )
    wiki_title = models.CharField(max_length=200, blank=True)
    wiki_url = models.CharField(max_length=200, blank=True)

    history = HistoricalRecords()

    def path(self):
        return reverse("machine_overview", kwargs={"machine_id": self.id})

    def url(self):
        return settings.BASE + self.path()

    def __str__(self):
        return self.name

    def useState(self, user):
        e = (
            Entitlement.objects.all()
            .filter(holder=user, permit=self.requires_permit)
            .first()
        )

        needs = MachineUseFlags.ACTIVE
        if self.requires_permit:
            needs |= MachineUseFlags.PERMIT
        if self.requires_form:
            needs |= MachineUseFlags.FORM
        if self.requires_permit and self.requires_permit.require_ok_trustee:
            needs |= MachineUseFlags.APPROVE
        if self.out_of_order:
            needs |= MachineUseFlags.OVERRIDE

        flags = 0
        if user.is_active:
            flags |= MachineUseFlags.ACTIVE
        if user.form_on_file:
            flags |= MachineUseFlags.FORM
        if e:
            flags |= MachineUseFlags.PERMIT
        if e and e.active:
            flags |= MachineUseFlags.APPROVE
        if self.canInstruct(user):
            flags |= MachineUseFlags.INSTRUCT
        if user.pettycash_cache.first():
            if user.pettycash_cache.first().balance > settings.MIN_BALANCE_FOR_CREDIT:
                flags |= MachineUseFlags.BUDGET

        # Normal users can only operate machines that are unlocked.
        # We may allow admins/some group to also operate unsafe
        # machines by doing something special here. So hence
        # we do not set the OVERRIDE bit here.
        #
        if user.is_privileged or self.canInstruct(user):
            flags |= MachineUseFlags.OVERRIDE

        return [needs, flags]

    def canOperate(self, user):
        if not user.is_active:
            return False
        if self.requires_form and not user.form_on_file:
            return False
        if not self.requires_permit:
            return True
        return self.requires_permit.hasThisPermit(user)

    def canInstruct(self, user):
        if not self.canOperate(user):
            return False
        if not self.requires_permit:
            return True
        if not self.requires_permit.permit:
            return True
        return self.requires_permit.permit.hasThisPermit(user)

    class Meta:
        ordering = ["name"]


# Special sort of create/get - where we ignore the issuer when looking for it.
# but add it in if we're creating it for the first time.
# Not sure if this is a good idea. Proly not. The other option
# would be to split entitelemtns into an entitelent and 1:N
# endorsements.
#
# I guess we could also trap this in the one or two places wheer
# we create an Entitlement.
#
class EntitlementManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        if "permit" in kwargs and "holder" in kwargs:
            e = (
                Entitlement.objects.all()
                .filter(permit=kwargs.get("permit"))
                .filter(holder=kwargs.get("holder"))
            )

            if e and e.count() >= 1:
                existing = e[0]

                if e.count() > 1:
                    logger.critical(
                        "IntigrityAlert: {} identical entitlement for {}.{}".format(
                            e.count(), kwargs.get("permit"), kwargs.get("holder")
                        )
                    )
                else:
                    logger.debug("Entity - trapped double create attempt: {}", existing)

                for k, v in kwargs.items():
                    setattr(existing, k, v)
                return existing, False
        return super(EntitlementManager, self).get_or_create(*args, **kwargs)


class EntitlementViolation(Exception):
    pass


class DoubleEntitlemenException(Exception):
    pass


class Entitlement(models.Model):
    active = models.BooleanField(
        default=False,
    )
    permit = models.ForeignKey(
        PermitType,
        on_delete=models.CASCADE,
        related_name="isRequiredToOperate",
    )
    holder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="isGivenTo",
    )
    issuer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="isIssuedBy",
        blank=True,
        null=True,
    )
    history = HistoricalRecords()
    objects = EntitlementManager()

    def __str__(self):
        return (
            str(self.holder)
            + "@"
            + self.permit.name
            + "(Trustee activated:"
            + yn(self.active)
            + ", Form:"
            + yn(self.holder.form_on_file)
            + ")"
        )

    # Bit of a temporary hack - we do not want to delete
    # the entitlements issued when a user is deleted; and we
    # also want to leave some  sort of audit of that persons
    # their name name; even if the main # user record is gone.
    #
    # However - while we can do things like 'on_delete=SET(function)'
    # -- we cannot pass any arguments; to that. So a bulk delete will
    # not trigger the save() where the issuer is set to None of
    # the Entitlement. And pre_save/delete here does not help
    # us either. So we do this as a special for now. Also bypassing
    # the normal save as it would block us (a non issuer is not allowed).
    #
    def delete_issuer_leaving_breadcrum(issuer):
        for e in Entitlement.objects.all().filter(issuer=issuer):
            reason = "Issuer %s no longer in the system" % (issuer)
            e.issuer = None
            e._change_reason = reason
            # Bypass below permit checks.
            super(Entitlement, e).save()

    def save(self, *args, **kwargs):
        current_site = Site.objects.get(pk=settings.SITE_ID)

        user = None
        if "request" in kwargs:
            request = kwargs["request"]
            del kwargs["request"]
            current_site = get_current_site(request)
            user = request.user
        else:
            if "bypass_user" in kwargs:
                user = kwargs["bypass_user"]
                del kwargs["bypass_user"]
                logger.info("Warning - bypass in operation.")

        # rely on the contraints to bomb out if there is nothing in kwargs and self. and self.
        #
        if not self.issuer and user:
            self.issuer = user

        issuer_permit = PermitType.objects.get(pk=self.permit.pk)

        if issuer_permit and not Entitlement.objects.filter(
            permit=issuer_permit, holder=self.issuer
        ):
            if not self.issuer or not self.issuer.is_staff:
                erm = "issuer {} of this entitelment lacks the entitlement {} to issue this to {} ({}).".format(
                    self.issuer,
                    issuer_permit,
                    user,
                    Entitlement.objects.filter(holder=self.issuer),
                )
                logger.critical(erm)
                raise EntitlementViolation(erm)
            logger.info(
                f"Entitlement.save(): STAFFF bypass of rule 'holder {self.issuer} cannot issue {self.permit} to {self.holder} as the holder lacks {issuer_permit}'"
            )

        if self.active is None:
            # See if we can fetch an older approval for same that may already have
            # been activated. And grandfather it in.
            try:
                e = Entitlement.objects.get(permit=self.permit, holder=self.holder)
                self.active = e.active
            except Exception as e:
                logger.warning(
                    "Failed to fetch an older entitlement: {}".format(str(e))
                )

        logger.debug(
            f"Entitlement: saving {self} -- with active:{self.active} and permit:{self.permit} ({self.permit.permit})"
        )
        # Current rule for pending is:
        if not self.active and self.permit.permit:
            try:
                context = {
                    "holder": self.holder,
                    "issuer": self.issuer,
                    "permit": self.permit,
                    "domain": current_site.domain,
                }

                subject = render_to_string(
                    "acl/notify_trustees_subject.txt", context
                ).strip()
                body = render_to_string("acl/notify_trustees.txt", context)

                EmailMessage(
                    subject,
                    body,
                    to=[self.issuer.email, settings.TRUSTEES, "dirkx@webweaving.org"],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                ).send()
                logger.error(
                    f"Entitlement: mail sent to {self.issuer} and the trustees"
                )
            except Exception as e:
                logger.critical("Failed to sent an email: {}".format(str(e)))

        # should we check for duplicates here too ?
        #
        return super(Entitlement, self).save(*args, **kwargs)


class RecentUse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    used = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        for e in RecentUse.objects.all().filter(machine=self.machine).order_by("-used"):
            if e.user == self.user:
                e.delete()
            else:
                break
        r = super(RecentUse, self).save(*args, **kwargs)

        cutoff = timezone.now() - datetime.timedelta(days=DAYS_USERS_TRACKED)
        for e in (
            RecentUse.objects.all()
            .filter(machine=self.machine, used__lt=cutoff)
            .order_by("-used")[MAX_USERS_TRACKED:]
        ):
            e.delete()
        return r

    def __str__(self):
        t = "<timestamp not yet set>"
        if self.used:
            t = self.used.strftime("%Y-%m-%d %H:%M:%S")
        return "{} used {} on {}".format(self.user, self.machine, t)


def yn(v):
    if v is None:
        return "?"
    if v:
        return "yes"
    return "no"


class Application(AbstractApplication):
    permit = models.ForeignKey(
        PermitType, on_delete=models.CASCADE, null=True, blank=True
    )


# This class tracks XS changes; it gets updated everytime something is
# touched that pertains to the ACL system. It is to aid the nodes in
# caching things & updating timely.
#
class ChangeTracker(models.Model):
    class Meta:
        verbose_name = "ACL and XS change counter"
        verbose_name_plural = verbose_name

    changed = models.DateTimeField(
        auto_now=True,
        help_text="Date and time of the last change in the XS control system",
    )
    count = models.IntegerField(
        default=0,
        help_text="Number of times something in the XS control ssytem changed",
    )


def change_tracker_counter():
    return ChangeTracker.objects.first()


def tagacl_change_tracker(sender, instance, **kwargs):
    # Avoid triggering on a last-login change; which is
    # generally done with (just) the last_login set
    # in the fields updated. See update_last_login() in
    # django.contrib.auth.models.
    #
    if "update_fields" in kwargs and kwargs["update_fields"] is not None:
        # Only skip if it is exactly this change. Other wise
        # err on the side of caution. E.g. for a new record
        # or some single REST change.
        #
        if len(kwargs["update_fields"]) == 1:
            if sender == User and "last_login" in kwargs["update_fields"]:
                return
            if sender == User and "password" in kwargs["update_fields"]:
                return
            if sender == Tag and "last_used" in kwargs["update_fields"]:
                return

    logger.debug("tagacl_change_tracker({},{},{})".format(sender, instance, kwargs))

    c = ChangeTracker.objects.first()
    if c is None:
        c = ChangeTracker()

    c.changed = timezone.now()
    c.count = c.count + 1
    c.save()


post_save.connect(tagacl_change_tracker, sender=Entitlement)  # actual ok bit
#
post_save.connect(tagacl_change_tracker, sender=Tag)  # People getting/loosing tags
post_save.connect(
    tagacl_change_tracker, sender=PermitType
)  # definiton of permits; e.g. stricter/more slack
post_save.connect(tagacl_change_tracker, sender=Machine)  # permit required
post_save.connect(
    tagacl_change_tracker, sender=User
)  # for waiver-form and status changes
