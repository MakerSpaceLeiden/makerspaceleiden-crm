from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "makerspace",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
