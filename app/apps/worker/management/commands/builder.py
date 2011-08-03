from app.apps.worker.relay import BuildRelay

from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.conf import settings
from optparse import make_option
import os

class Command(BaseCommand):
    help = 'Start the build worker process'
    can_import_settings = True
    
    def handle(self, *args, **options):
        from django.conf import settings
        relay_kwargs = {
            'host': settings.BUILDRELAY_WEBSOCKET_HOST,
            'port': settings.BUILDRELAY_WEBSOCKET_PORT,
            'redis_opts':{
                'host': settings.REDIS_HOST,
                'port': settings.REDIS_PORT,
                'db': settings.REDIS_DB
            }
        }
        print u"listening on http://%s:%s" % (settings.BUILDRELAY_WEBSOCKET_HOST,
            settings.BUILDRELAY_WEBSOCKET_PORT)
        relay = BuildRelay(**relay_kwargs)
