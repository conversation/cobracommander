from django.db.models.signals import post_save
from django.dispatch import receiver

from ..project.models import Project
from .models import Target


@receiver(post_save, sender=Project, dispatch_uid="create_master_build_target_for_project")
def create_master_build_target_for_project(sender, **kwargs):
    master = Target(project=kwargs.get('instance'), branch='master').save()