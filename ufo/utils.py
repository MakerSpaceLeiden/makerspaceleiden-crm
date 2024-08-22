import logging
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def emailUfoInfo(itemsToAttachImage, template, toinform=[], context={}):
    to = {}
    for person in toinform:
        to[person] = True

    # We use a dict rather than an array to prune any duplicates.
    to = to.keys()

    context["base"] = settings.BASE
    context["items"] = itemsToAttachImage
    context["count"] = len(itemsToAttachImage)

    part2 = None

    if len(itemsToAttachImage) > 1:
        msg = MIMEMultipart("alternative")
        subject = render_to_string("ufo/{}_bulk_subject.txt".format(template), context)

        part1 = MIMEText(
            render_to_string("ufo/{}_bulk.txt".format(template), context), "plain"
        )
        part2 = MIMEMultipart("related")
        part2.attach(
            MIMEText(
                render_to_string("ufo/{}_bulk.html".format(template), context), "html"
            )
        )

        for i in itemsToAttachImage:
            ext = i.image.name.split(".")[-1]
            attachment = MIMEImage(i.image.thumbnail.read(), ext)
            attachment.add_header("Content-ID", str(i.pk))
            attachment.add_header(
                "Content-Disposition", 'inline; filename="' + i.image.name + '"'
            )
            part2.attach(attachment)
    else:
        item = itemsToAttachImage[0]
        msg = MIMEMultipart("mixed")
        subject = render_to_string("ufo/{}_subject.txt".format(template), context)

        part1 = MIMEText(
            render_to_string("ufo/{}.txt".format(template), context), "plain"
        )
        part2 = MIMEMultipart("mixed")

        ext = item.image.name.split(".")[-1]
        attachment = MIMEImage(item.image.medium.read(), ext)
        attachment.add_header("Content-ID", str(item.pk))
        part2.attach(attachment)

    msg.attach(part1)
    msg.attach(part2)

    email = EmailMessage(
        subject.strip(), None, to=to, from_email=settings.DEFAULT_FROM_EMAIL
    )
    email.attach(msg)
    email.send()
