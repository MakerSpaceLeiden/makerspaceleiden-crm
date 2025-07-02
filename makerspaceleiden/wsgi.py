"""
WSGI config for makerspaceleiden project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from selfservice.aggregator_adapter import initialize_aggregator_adapter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "makerspaceleiden.settings")

_application = get_wsgi_application()


def application(environ, start_response):
    initialize_aggregator_adapter(
        os.environ.get("AGGREGATOR_BASE_URL", "http://127.0.0.1:5000"),
        os.environ.get("AGGREGATOR_USERNAME", "user"),
        os.environ.get("AGGREGATOR_PASSWORD", "pass"),
    )
    return _application(environ, start_response)
