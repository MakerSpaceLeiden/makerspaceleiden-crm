from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy,reverse
from stdimage.models import StdImageField

from django.db.models.signals import pre_delete, pre_save
from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback

from makerspaceleiden.utils import upload_to_pattern

import re

GDPR_ESCALATED_TIMESPAN = 60 * 10 
if hasattr(settings,'GDPR_ESCALATED_TIMESPAN'):
    GDPR_ESCALATED_TIMESPAN = settings.GDPR_ESCALATED_TIMESPAN

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class AuditRecord:
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=400)
    recorded = models.DateTimeField(auto_now_add=True, db_index=True)

    def last(self, user):
       try:
          return self.objects.all().filter(user = user).latest('recorded')
       except DoesNotExist:
          return None

class User(AbstractUser):
    class Meta:
        ordering = ['first_name', 'last_name']

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'telegram_user_id']

    username = None

    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=40, blank=True, null=True, help_text="Optional; only visible to the trustees and board delegated administrators")
    image = StdImageField(upload_to=upload_to_pattern, variations=settings.IMG_VARIATIONS, validators=settings.IMG_VALIDATORS, blank=True, default='')
    form_on_file = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    telegram_user_id = models.CharField(max_length=200, blank=True, null=True, help_text="Optional; Telegram User ID; only visible to the trustees and board delegated administrators")
    uses_signal = models.BooleanField(default=False)
    always_uses_email = models.BooleanField(default=False, help_text="Receive notifications via email even when using a chat BOT")

    history = HistoricalRecords()
    objects = UserManager()

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    def name(self):
        return self.__str__()

    def path(self):
        return  reverse('overview', kwargs = { 'member_id' :  self.id })

    def url(self):
        return  settings.BASE + self.path()

    def is_privileged(self, request = None, action = None):
        if self.is_superuser():
           return True
        if not self.is_staff() or not request:
           return True
        last = AuditRecord.last(self):
        if last == None or last + GDPR_ESCALATED_TIMESPAN > > datetime.now():
           return False
        if action:
           # log action.. 
           # Also extend the priv-time ?
           pass 
        return true

    def can_escalate_to_priveleged(self):
        return self.is_staff() or self.is_superuser()

    def escalate_to_priveleged(self, request, action):
        ar = AuditRecord(user = self, action = action)

class Tag(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=30, unique=True) #, editable = False)
    description = models.CharField(max_length=300, blank=True, null=True)

    last_used = models.DateTimeField(blank=True, null = True) # , editable = False)

    history = HistoricalRecords()

    def __str__(self):
        return self.tag + ' (' + str(self.owner) + ')'

def clean_tag_string(tag):
    try:
       bts = [ b for b in re.compile('[^0-9]+').split(tag.upper())
                   if b is not None and b is not '' and int(b) >=0 and int(b) < 256]
       if len(bts) < 3:
           return None
       return '-'.join(bts)

    except ValueError as e:
       pass

    return None

# Handle image cleanup.
pre_delete.connect(pre_delete_delete_callback, sender=User)
pre_save.connect(pre_save_delete_callback, sender=User)
