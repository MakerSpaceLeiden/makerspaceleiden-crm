import os
import sys

from moneyed import EUR, Money

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
FORCE_SCRIPT_NAME = os.environ.get("FORCE_SCRIPT_NAME", "/")
LOGIN_URL = os.environ.get("LOGIN_URL", "/crm/login/")
LOGIN_REDIRECT_URL = os.environ.get("LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = os.environ.get("LOGOUT_REDIRECT_URL", "/")
STATIC_URL = os.environ.get("STATIC_URL", "/crm-static/")
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/usr/local/makerspaceleiden-crm/var/media")
DEBUG = False
with open("/etc/crm_secret_key.txt") as f:
    SECRET_KEY = f.read().strip()
SECURE_HSTS_SECONDS = 120
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "OPTIONS": {
            "read_default_file": "/usr/local/makerspaceleiden-crm/makerspaceleiden/my.cnf",
        },
    }
}

EMAIL_BACKEND = "django_sendmail_backend.backends.EmailBackend"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "log_to_stdout": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.environ.get("LOG_FILE_NAME", "/var/log/crm/crm-debug.log"),
            "maxBytes": 1024 * 1024,
            "backupCount": 10,
            "formatter": "standard",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "propagate": False,
        },
        "daphne": {
            "handlers": ["file"],
            "propagate": False,
        },
        "django.server": {
            "handlers": ["file"],
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file"],
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file"],
            "propagate": False,
        },
        "django.db": {
            "handlers": ["file"],
            "propagate": False,
        },
        "django.template": {
            "handlers": ["file"],
            "propagate": False,
        },
        "commands": {
            "handlers": ["log_to_stdout"],
            "level": "DEBUG",
            "propagate": False,
        },
        "mailinglists": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "": {
            "handlers": ["file"],
            "propagate": False,
        },
    },
}
ALSO_INFORM_EMAIL_ADDRESSES = ["deelnemers@lists.makerspaceleiden.nl"]

# v1 legacy
DOORS = 3
with open("/etc/crm_v1_ss.txt") as f:
    LV1_SECRET = f.read().strip()

with open("/etc/crm_uk_bearer_secret.txt") as f:
    UT_BEARER_SECRET = f.read().strip()

GRAND_AMNESTY = False

PETTYCASH_IBAN = "NL30TRIO0197694519"

POT_ID = 63
NONE_ID = 217

# Increased; As per discussion with treasurer 2025-04-02
#
MAX_PAY_API = Money(35.00, EUR)
MAX_PAY_CRM = Money(300.00, EUR)
