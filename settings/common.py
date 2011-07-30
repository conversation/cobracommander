from .default import *

PROJECT_NAME = 'cobracommander'
SERVER_NAME = ''

ADMINS = (('Justin Morris', 'error-reports@pixelbloom.com'),)
MANAGERS = ADMINS
EMAIL_SUBJECT_PREFIX = '[%s_production] ' % PROJECT_NAME

SECRET_KEY = 'h=ku=biuz1-4_%5z0j5&fr3io(7&%_f+9028cidh&3cal^mlmj'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '%s_production' % PROJECT_NAME,
        'TEST_NAME':'%s_test' % PROJECT_NAME
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.static',
    'django.core.context_processors.media',
    'django.core.context_processors.csrf',
    'django.core.context_processors.request',
)

TEMPLATE_TAGS = (
    'django.templatetags.future',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'dogslow.WatchdogMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.markup',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # external
    'south',
    'compressor',
    'gunicorn',
    'typogrify',
    'django_html',
    'sorl.thumbnail',
    'sentry',
    'sentry.client',
    'django_nose',
    'poseur',
    
    # internal
    'app.apps.project',
    'app.apps.build',
)
