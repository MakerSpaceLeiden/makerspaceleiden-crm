FORCE_SCRIPT_NAME='/crm'
LOGIN_URL = '/crm//admin/login/'
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

LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                 'file': {
                      'level': 'INFO',
                      'class': 'logging.FileHandler',
                      'filename': '/var/log/crm-debug.log',
                 },
            },
            'loggers': {
                  'django': {
                      'handlers': ['file'],
                      'level': 'DEBUG',
                      'propagate': True,
                  },
            },
}

ALSO_INFORM_EMAIL_ADDRESSES = [ 'deelnemers@mailman.makerspaceleiden.nl' ]
