from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "makerspace",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
