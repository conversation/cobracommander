from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import datetime

from ..project.models import Project


class Target(models.Model):
    """(Target description)"""
    
    project = models.ForeignKey(Project)
    branch = models.CharField(blank=False, max_length=100)
    
    class Meta:
        unique_together = ('project', 'branch')
    
    def __unicode__(self):
        return u"%s:%s" % (self.project, self.branch)