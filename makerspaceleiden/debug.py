# For DEVLOPMNET  - fake bacend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MEDIA_ROOT="/tmp"
UT_BEARER_SECRET='Foo'
DOORS=7

import os
if 'ML_ADMINURL' in os.environ:
   ML_ADMINURL = os.environ['ML_ADMINURL']
if 'ML_PASSWORD' in os.environ:
   ML_PASSWORD = os.environ['ML_PASSWORD']
