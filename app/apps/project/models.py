from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import datetime

from ..build.models import Build


class Project(models.Model):
    """(Project description)"""
    
    name = models.CharField(blank=False, max_length=100)
    name_slug = models.SlugField(blank=False, db_index=True)
    repo_url = models.CharField(blank=False, max_length=255)
    description = models.TextField(blank=True)
    builds = models.ManyToManyField(Build)
    
    def __unicode__(self):
        return u"%s" % (self.name)
    
    @models.permalink
    def get_absolute_url(self):
        return ('project:show', (), {
            'project_name_slug':self.name_slug
        })