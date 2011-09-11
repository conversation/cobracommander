from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.conf import settings
from optparse import make_option
import os

from app.apps.worker.build_relay import BuildRelay


class Command(BaseCommand):
    help = 'Start the build worker process'
    can_import_settings = True
    
    def handle(self, *args, **options):
        relay = BuildRelay()