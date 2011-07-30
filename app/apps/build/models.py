from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import datetime


class Build(models.Model):
    """(Project description)"""
    
    STATE_CHOICES = (
        ("a", "pending",),
        ("b", "running",),
        ("c", "pass",),
        ("d", "fail",),
    )
    
    ref = models.CharField(blank=False, max_length=100, db_index=True)
    state = models.CharField(blank=True, max_length=1, default="a", choices=STATE_CHOICES)
    created_datetime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    start_datetime = models.DateTimeField(blank=True)
    end_datetime = models.DateTimeField(blank=True)
    
    def __unicode__(self):
        return u"%s" % (self.ref)
    
    @models.permalink
    def get_absolute_url(self):
        return ('build:show', (), {
            'build_ref':self.ref
        })

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


