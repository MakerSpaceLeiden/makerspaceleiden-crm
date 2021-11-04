from lxml import etree
import re
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

from moneyed import Money, EUR

import sys, os
import datetime


def camt53_process(file):
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
        results.append(process(e, namespaces))

    return results


def process(e, namespaces):
    ref = e.xpath("camt:NtryRef/text()", namespaces=namespaces)[0]
    out = {}
    out["ref"] = ref
    out["success"] = False

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
    iban_str = "%s*****%s" % (iban_str[0:8], iban_str[-3:])

    details = e.xpath(
        "camt:NtryDtls/camt:TxDtls/camt:AddtlTxInf/text()", namespaces=namespaces
    )
    if len(details):
        details = details[0]
    else:
        details = ""

    out["iban_str"] = iban_str
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

    matches = [
        w
        for w in ["space", "tegoed", "zwarte pot", "zwartepot", "storting", "spacepot"]
        if w in details.lower()
    ]
    if len(matches) < 2:
        out["msg"] = "Skipping - not enough trigger words"
        return out

    m = re.search(r"\b(\d+)\b", details)
    if not m:
        out["msg"] = "ERROR Skipping - no uid"
        out["error"] = True
        return out

    try:
        uid = int(m.group(0))
    except:
        out["msg"] = "ERROR - Skipping - uid could not be parsed"
        out["error"] = True
        return out

    MAX_UID = 10000
    if uid <= 0 or uid > MAX_UID:
        out["msg"] = "ERROR - Skipping no usabable user id"
        out["error"] = True
        return out

    try:
        user = User.objects.get(pk=uid)
        out["user"] = user
    except:
        out["msg"] = "ERROR - Skipping, no user with uid=%d" % uid
        out["error"] = True
        return out

    try:
        h = PettycashTransaction.history.filter(Q(history_change_reason__contains=ref))
        if h.count() > 0:
            out["msg"] = (
                "ERROR - Skipping, already %d transction(s) in the history with identifier=%s: first:%s"
                % (h.count(), ref, h.first())
            )
            out["error"] = True
            return out
    except ObjectDoesNotExist as e:
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
