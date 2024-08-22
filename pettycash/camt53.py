import base64
import hashlib
import hmac
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from lxml import etree
from moneyed import EUR, Money

from members.models import User
from pettycash.models import PettycashTransaction


def camt53_process(
    file,
    triggerwords=["space", "tegoed", "zwarte pot", "zwartepot", "storting", "spacepot"],
    uidmapping=(),
    nouidcheck=False,
):
    print(file)
    xmlparser = etree.XMLParser(
        ns_clean=True, remove_blank_text=True, remove_comments=True, no_network=True
    )
    triodos = etree.parse(file, xmlparser)
    results = []

    nsmap = triodos.getroot().nsmap
    namespaces = {"camt": nsmap[None]}

    for e in triodos.xpath(
        "/camt:Document/camt:BkToCstmrStmt/camt:Stmt/camt:Ntry", namespaces=namespaces
    ):
        results.append(process(e, namespaces, triggerwords, uidmapping, nouidcheck))

    return results


def process(e, namespaces, triggerwords, uidmapping, nouidcheck=False, maskiban=True):
    out = {}

    ref = e.xpath("camt:NtryRef/text()", namespaces=namespaces)[0]
    out["ref"] = ref
    out["success"] = False

    dte = e.xpath("camt:BookgDt/camt:Dt/text()", namespaces=namespaces)[0]
    out["date"] = dte

    tpe = e.xpath("camt:CdtDbtInd/text()", namespaces=namespaces)[0]
    if tpe == "CRDT":
        credit = True
    else:
        credit = False

    prop = e.xpath("camt:BkTxCd/camt:Prtry/camt:Cd/text()", namespaces=namespaces)[0]
    if prop == "KN":
        # skip kosten
        out["msg"] = "Skipping - bank-charge"
        return out

    if prop != "PO" and prop != "ET":
        out["msg"] = "Warning unknown type found: %s, skipping" % prop
        return out

    amount_str = e.xpath("camt:Amt/text()", namespaces=namespaces)[0].strip()
    if not credit:
        amount_str = "-" + amount_str

    # for some odd reason - we see a Cbtr entry on a debit.
    name_str = next(
        item
        for item in [
            e.xpath(
                "camt:NtryDtls/camt:TxDtls/camt:RltdPties/camt:Cdtr/camt:Nm/text()",
                namespaces=namespaces,
            )
            + e.xpath(
                "camt:NtryDtls/camt:TxDtls/camt:RltdPties/camt:Dbtr/camt:Nm/text()",
                namespaces=namespaces,
            )
        ]
        if item is not None and item != ""
    )[0]

    iban_str = next(
        item
        for item in [
            e.xpath(
                "camt:NtryDtls/camt:TxDtls/camt:RltdPties/camt:DbtrAcct/camt:Id/camt:IBAN//text()",
                namespaces=namespaces,
            )
            + e.xpath(
                "camt:NtryDtls/camt:TxDtls/camt:RltdPties/camt:CdtrAcct/camt:Id/camt:IBAN//text()",
                namespaces=namespaces,
            )
        ]
        if item is not None and item != ""
    )[0]

    # Rather than hash just the IBAN; we mix in our (production) secret key to make it
    # a bit more resistant against, say, a dictionary search based on a list of all
    # Dutch bank accounts (these things are floating around on the internet).
    #
    iban_keyed_hash = base64.b64encode(
        hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            iban_str.encode("ASCII"),
            hashlib.sha256,
        ).digest()
    )

    valdigits = 0
    try:
        valdigits = int(iban_str[2:4])
    except Exception as e:
        # out["msg"] = "Skipping - could not convert/parse IBAN for check digits."
        # return out
        valdigits = 0

    iban_raw = iban_str
    if maskiban:
        iban_str = "%s*****%s" % (iban_str[0:8], iban_str[-3:])

    details = e.xpath(
        "camt:NtryDtls/camt:TxDtls/camt:AddtlTxInf/text()", namespaces=namespaces
    )
    if len(details):
        details = details[0]
    else:
        details = ""

    out["iban_str"] = iban_str
    out["iban_keyed_has"] = iban_keyed_hash
    out["iban_valdigits"] = valdigits
    out["name_str"] = name_str
    out["details"] = details

    if not credit:
        out["msg"] = "Skipping - credit"
        return out

    out["amount_str"] = amount_str
    try:
        amount = float(amount_str)
        amount = Money(amount, EUR)
    except Exception as e:
        out["msg"] = "ERROR Skipping - amount could not be parsed %s" % e
        out["error"] = True
        return out

    out["amount"] = amount

    out["amount_str"] = "%s" % amount
    if amount < Money(0, EUR) or amount > settings.MAX_PAY_DEPOSITI:
        out["msg"] = (
            "ERROR Skipping - amount not between 0 and %s" % settings.MAX_PAY_DEPOSITI
        )
        out["error"] = True
        return out

    matches = [w for w in triggerwords if w in details.lower()]
    if len(matches) < 1:
        out["msg"] = "Skipping - not enough trigger words "
        return out

    uid = 0
    if uidmapping:
        hits = [line for line in uidmapping.keys() if iban_raw in line]
        if len(hits) == 0:
            out["msg"] = "ERROR Skipping - no ibanstr to map to uid"
            out["error"] = True
            return out
        if len(hits) > 1:
            out["msg"] = "ERROR Skipping - {} appears for multiple UIDs".format(
                iban_str
            )
            out["error"] = True
            return out
        uid = int(uidmapping[hits[0]])

    if uid == 0:
        m = re.search(r"\b(\d+)\b", details)
        if m:
            try:
                uid = int(m.group(0))
            except Exception:
                out["msg"] = "ERROR - Skipping - uid could not be parsed"
                out["error"] = True
                return out

    MAX_UID = 10000
    if uid <= 0 or uid > MAX_UID:
        out["msg"] = "ERROR - Skipping -- no usabable user id"
        out["error"] = True
        return out

    if nouidcheck:
        out["uid"] = uid
        user, created = User.objects.get_or_create(email=uid)
        user.last_name = name_str
    else:
        try:
            user = User.objects.get(pk=uid)
            out["user"] = user
        except Exception:
            out["msg"] = "ERROR - Skipping, no user with uid=%d" % uid
            out["error"] = True
            return out

        try:
            h = PettycashTransaction.history.filter(
                Q(history_change_reason__contains=ref)
            )
            if h.count() > 0:
                out["msg"] = (
                    "ERROR - Skipping, already %d transction(s) in the history with identifier=%s: first:%s"
                    % (h.count(), ref, h.first())
                )
                out["error"] = True
                return out
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            out["msg"] = "ERROR - Skipping, error looking up '%s': %s" % (ref, e)
            out["error"] = True
            return out

    out["success"] = True
    out["description"] = "Deposit by %s, %s" % (name_str, iban_str)
    out["msg"] = "PROCESSED -- deposit %s for user %s from %s" % (
        amount,
        user,
        iban_str,
    )

    return out
