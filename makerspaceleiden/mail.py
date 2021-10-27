from django.shortcuts import render, redirect
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import datetime
import logging

logger = logging.getLogger(__name__)


def emailPlain(template, toinform=[], context={}):
    # Weed out duplicates.
    to = list(set(toinform))

    context["base"] = settings.BASE

    body = render_to_string(template, context).split("\n")
    subject = body[0].rstrip()
    body = "\n".join(body[1:])

    msg = MIMEMultipart("alternative")

    part1 = MIMEText(body, "plain")
    msg.attach(part1)

    part2 = MIMEMultipart("related")
    part2.attach(
        "<html><head><title>%s</title></head><body><pre>%s</pre></body><html>"
        % (subject, body),
        "html",
    )
    msg.attach(part2)

    email = EmailMessage(
        subject.strip(), None, to=to, from_email=settings.DEFAULT_FROM_EMAIL
    )
    email.attach(msg)
    email.send()
