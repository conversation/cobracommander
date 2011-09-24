import os, sys

# Paths and path helpers
# -----------------------------------------------
def ensure_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

here = lambda * x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), *x))
ENV_ROOT = here('../../../')
PROJECT_ROOT = here('../')
APPS_ROOT = here('../apps/')

environment = lambda * x: os.path.abspath(os.path.join(ENV_ROOT, *x))
apps = lambda * x: os.path.abspath(os.path.join(APPS_ROOT, *x))
project = lambda * x: os.path.abspath(os.path.join(PROJECT_ROOT, *x))

PROJECT_MODULE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')).split('/')[-1]
sys.path.append(PROJECT_ROOT)
sys.path.append(environment('project'))

TMP_ROOT = ensure_exists(environment('tmp'))
BUILD_ROOT = ensure_exists(environment('tmp', 'builds'))
MEDIA_ROOT = ensure_exists(environment('tmp', 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = project('static')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'


# Generic settings
# -----------------------------------------------
SITE_ID = 1
INTERNAL_IPS = ('127.0.0.1',)
DEBUG = False
TEMPLATE_DEBUG = True
SEND_BROKEN_LINK_EMAILS = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-au'
ROOT_URLCONF = '%s.settings.urls' % PROJECT_MODULE
IGNORABLE_404_STARTS = ('mail.pl', 'mailform.pl', 'mail.cgi', 'mailform.cgi', 'favicon.ico', 'favicon.ico/', '.php')
DEFAULT_FROM_EMAIL = 'cobracommander@localhost'
SERVER_EMAIL = 'cobracommander@localhost'
BUILD_FILE_NAME = 'buildfile'


# Authentication settings
# -----------------------------------------------
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'


# Templates settings
# -----------------------------------------------
TEMPLATE_DIRS = (project('templates'),)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)


# Staticfiles settings
# -----------------------------------------------
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)


# Cache backend settings
# -----------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': ensure_exists(environment('tmp', 'cache')),
    }
}


# Logging settings
# -----------------------------------------------
def logging_filename():
    logdir = os.path.join(ENV_ROOT, 'logs')
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    return os.path.join(logdir, '%s.log' % PROJECT_MODULE)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(levelname)s %(asctime)s |'
                       '%(pathname)s:%(lineno)d (in %(funcName)s) |'
                       ' %(message)s ')
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(ensure_exists(environment('logs/')), '%s.log' % PROJECT_MODULE),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        }
    }
}
