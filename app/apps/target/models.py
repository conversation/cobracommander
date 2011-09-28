from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import datetime

from ..build.models import Build


class Target(models.Model):
    """(Target description)"""
    builds = models.ManyToManyField(Build, blank=True, null=True)
    branch = models.CharField(blank=False, max_length=100)

    class Meta:
        pass

    def __unicode__(self):
        return u"%s" % self.branch

    @models.permalink
    def get_absolute_url(self):
        return ('build:show', (), {
            'branch':self.branch,
            'project_name_slug':self.project_name_slug
        })
