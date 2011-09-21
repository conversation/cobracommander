from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
import datetime

from ..target.models import Target


class Build(models.Model):
    """(Project description)"""

    STATE_CHOICES = (
        ("a", "pending",),
        ("b", "running",),
        ("c", "pass",),
        ("d", "fail",),
    )

    target = models.ForeignKey(Target)
    state = models.CharField(blank=True, max_length=1, default="a", choices=STATE_CHOICES)
    created_datetime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    log = models.TextField(blank=True)

    def __unicode__(self):
        return u"%s" % (self.target)

    @models.permalink
    def get_absolute_url(self):
        # TODO: LOL, fix this!
        return ('build:show', (), {
            'build_id':self.id,
            'project_name_slug':self.target.project.name_slug
        })

    @models.permalink
    def get_stop_url(self):
        # TODO: LOL, fix this!
        return ('build:stop', (), {
            'build_id':self.id,
            'project_name_slug':self.target.project.name_slug
        })


class Step(models.Model):
    """Sup"""

    STATE_CHOICES = (
        ("a", "pending",),
        ("b", "running",),
        ("c", "pass",),
        ("d", "fail",),
    )

    build = models.ForeignKey(Build)
    command = models.CharField(blank=False, max_length=255)
    created_datetime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    output = models.TextField(blank=True)
    state = models.CharField(blank=True, max_length=1, default="a", choices=STATE_CHOICES)

    def __unicode__(self):
        return u"%s" % (self.command)
