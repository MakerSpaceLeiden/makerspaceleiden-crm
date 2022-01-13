from django.shortcuts import render, redirect
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.charset import Charset, QP
import email.mime, email.mime.nonmultipart, email.charset

import datetime
import logging
import re

logger = logging.getLogger(__name__)


def flatten(t):
    out = []
    if isinstance(t, list):
        for i in t:
            if isinstance(i, list):
                out.extend(flatten(i))
            else:
                out.append(i)
    else:
        out.append(t)
    return out


def emails_for_group(group):
    return list(
        User.objects.all().filter(groups__name=group).values_list("email", flat=True)
    )


def emailPlain(template, subject=None, toinform=[], context={}, attachments=[]):
    # try to stick to rfc822 (django default is base64) religiously; also
    # as it helps with spam filters.
    cs = Charset("utf-8")
    cs.body_encoding = QP

    # Weed out duplicates.
    to = list(set(flatten(toinform)))

    context["base"] = settings.BASE

    body = render_to_string(template, context)

    if not subject:
        body = body.split("\n")
        subject = body[0].rstrip()
        subject = re.sub("^Subject:\s+", string=subject, repl="", flags=re.IGNORECASE)
        body = "\n".join(body[1:])

    body_html = (
        "<html><head><title>%s</title></head><body><pre>%s</pre></body><html>"
        % (subject, body)
    )

    msg = MIMEMultipart("alternative")

    part1 = MIMEText(body, "plain", _charset=cs)

    part2 = MIMEMultipart("related")
    part2.attach(MIMEText(body_html, "html", _charset=cs))

    email = EmailMessage(
        subject.strip(), None, to=to, from_email=settings.DEFAULT_FROM_EMAIL
    )

    for attachment in attachments:
        part2.attach(attachment)

    msg.attach(part1)
    msg.attach(part2)

    email.attach(msg)
    email.send()
