from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import datetime

from ..build.models import Build


class Project(models.Model):
    """(Project description)"""
    
    name = models.CharField(blank=False, max_length=100)
    name_slug = models.SlugField(blank=False, db_index=True)
    repo_url = models.URLField(blank=True, verify_exists=True, db_index=True)
    branch = models.CharField(blank=False, max_length=100, default="master")
    description = models.TextField(blank=True)
    builds = models.ManyToManyField(Build, blank=True, null=True)
    created_datetime = models.DateTimeField(blank=False, default=datetime.datetime.now)
    
    class Meta:
        unique_together = ("name_slug", "branch")
    
    def __unicode__(self):
        return u"%s" % (self.name)
    
    @models.permalink
    def get_absolute_url(self):
        return ('project:show', (), {
            'project_name_slug':self.name_slug
        })