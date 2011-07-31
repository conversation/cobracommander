import os
from ..default import *
from ..common import *
from ..external import *

# set ENV_ROOT using pwd in dev so as to not cock up the symlinks
ENV_ROOT = os.path.abspath(os.path.join(os.path.abspath(os.getenv('PWD')), '../../'))

SERVER_NAME = '%s.local' % PROJECT_NAME

DEBUG = True
TEMPLATE_DEBUG = DEBUG


# MIDDLEWARE
# --------------------------------------
DEVELOPMENT_MIDDLEWARE_CLASSES = [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES += DEVELOPMENT_MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)


# INSTALLED_APPS
# --------------------------------------
DEVELOPMENT_APPS = [
    'django_extensions',
    'debug_toolbar'
]
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS += DEVELOPMENT_APPS
INSTALLED_APPS = tuple(INSTALLED_APPS)


# database
# --------------------------------------
DATABASES['default']['NAME'] = '%s_development' % PROJECT_NAME


# celery
# --------------------------------------
CELERY_SEND_TASK_ERROR_EMAILS = True


# debug toolbar config
# --------------------------------------
def show_dev_toolbar(request):
    from django.conf import settings 
    if request.META['REMOTE_ADDR'] in settings.INTERNAL_IPS:
        if 'admin' not in request.META['PATH_INFO'].split('/'):
            return True
    return False

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': show_dev_toolbar,
    'EXTRA_SIGNALS': [],
    'HIDE_DJANGO_SQL': True,
    'SHOW_TEMPLATE_CONTEXT': True,
    'TAG': 'div'
}