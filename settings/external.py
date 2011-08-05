from .default import *


# nose test runner settings
# -----------------------------------------------
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--with-django', '--stop']


# celery config
# -----------------------------------------------
import djcelery
djcelery.setup_loader()
CELERY_TRACK_STARTED = True
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_MAX_TASKS_PER_CHILD = 1
CELERYD_CONCURRENCY = 1
CELERYD_PREFETCH_MULTIPLIER = 1
BROKER_BACKEND = "djkombu.transport.DatabaseTransport"
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_IMPORTS = (
    "app.apps.worker.tasks",
)


# relay config
# -----------------------------------------------
BUILDRELAY_WEBSOCKET_HOST = "localhost"
BUILDRELAY_WEBSOCKET_PORT = 9991
REDIS_DATABASE = {
    'host':"localhost",
    'port':6379,
    'db':0
}


# compressor
# -----------------------------------------------
COMPRESS = True # Automatically set to the opposite of DEBUG if NOT set
if DEBUG:
    COMPRESS_DEBUG_TOGGLE = 'nocompress' # GET arg that will turn of compression - only in dev mode
COMPRESS_REBUILD_TIMEOUT = 0
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = 'cache'
COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'
COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',]
COFFEESCRIPT_EXECUTABLE = 'coffee'
SCSS_EXECUTABLE = 'sass'
COMPRESS_JS_FILTERS = ['compressor.filters.jsmin.JSMinFilter']
COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', '%s --compile --stdio' % COFFEESCRIPT_EXECUTABLE),
    ('text/x-scss', '%s {infile} {outfile}' % SCSS_EXECUTABLE),
)