FORCE_SCRIPT_NAME='/crm'
LOGIN_URL = '/crm/login/'
LOGIN_REDIRECT_URL = '/crm/'
LOGOUT_REDIRECT_URL = '/crm/'
STATIC_URL = '/crm-static/'
MEDIA_ROOT = '/usr/local/makerspaceleiden-crm/var/media'
DEBUG=False
with open('/etc/crm_secret_key.txt') as f:
        SECRET_KEY = f.read().strip()
SECURE_HSTS_SECONDS=120
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
X_FRAME_OPTIONS='DENY'
SECURE_SSL_REDIRECT=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True

DATABASES = {
            'default': {
                        'ENGINE': 'django.db.backends.mysql',
                        'OPTIONS': {
                            'read_default_file': '/usr/local/makerspaceleiden-crm/makerspaceleiden/my.cnf',
                       },
            }
}

EMAIL_BACKEND = 'django_sendmail_backend.backends.EmailBackend'

import sys

LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'handlers': {
                 'log_to_stdout': {
                     'level': 'DEBUG',
                     'class': 'logging.StreamHandler',
                     'stream': sys.stdout,
                     },
                 'file': {
                      'level': 'INFO',
                      'class': 'logging.handlers.RotatingFileHandler',
                      'filename': '/var/log/crm/crm-debug.log',
                      'maxBytes': 1024*1024, 
                      'backupCount': 10,
                      'formatter': 'standard',
                 },
                 'console': {
                      'level': 'DEBUG',
                      'class': 'logging.StreamHandler',
                      'formatter': 'standard',
                 },
            },
            'loggers': {
                  'django': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'django.server': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'django.request': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'django.security': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'django.db': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'django.template': {
                      'handlers': ['file'],
                      'propagate': True,
                  },
                  'commands': {
                      'handlers': ['log_to_stdout'],
                       'level': 'DEBUG',
                       'propagate': True,
                   },
            },
}
ALSO_INFORM_EMAIL_ADDRESSES = [ 'deelnemers@mailman.makerspaceleiden.nl' ]

# v1 legacy
DOORS=3
with open('/etc/crm_v1_ss.txt') as f:
        LV1_SECRET= f.read().strip()

with open('/etc/crm_uk_bearer_secret.txt') as f:
        UT_BEARER_SECRET = f.read().strip()

GRAND_AMNESTY = False

ML_ADMINURL = 'https://mailman.makerspaceleiden.nl/mailman'
with open('/etc/crm_ml_secret.txt') as f:
    ML_PASSWORD = f.read().strip()


