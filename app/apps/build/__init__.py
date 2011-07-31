from django.db.models.signals import post_save
from .signals import trigger_build
from .models import Build

post_save.connect(trigger_build, sender=Build,
    dispatch_uid="trigger-new-build")