from django.urls import reverse

from makerspaceleiden.utils import generate_signed_str


def get_avatar_url(pk):
    return reverse("generate-fake-mugshot", args=[pk])


def get_avatar_url_signed(pk):
    signed_pk = generate_signed_str(pk)
    return reverse("generate-fake-mugshot-signed-urls", args=[signed_pk])
