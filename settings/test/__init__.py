import os
from ..development import *


# set ENV_ROOT using pwd in dev so as to not cock up the symlinks
ENV_ROOT = os.path.abspath(os.path.join(os.path.abspath(os.getenv('PWD')), '../../'))

SERVER_NAME = '%s-test.local' % PROJECT_NAME

DEBUG = False
TEMPLATE_DEBUG = True

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.remove('debug_toolbar.middleware.DebugToolbarMiddleware')
MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)

LETTUCE_SERVER_PORT = 7000
LETTUCE_AVOID_APPS = (
    'compressor',
    'gunicorn',
    'typogrify',
    'django_html',
    'django_nose',
    'django_extensions',
)

# INSTALLED_APPS
# --------------------------------------
TESTING_APPS = [
    'lettuce.django'
]
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS += TESTING_APPS
INSTALLED_APPS.remove('south')
INSTALLED_APPS.remove('debug_toolbar')
INSTALLED_APPS = tuple(INSTALLED_APPS)