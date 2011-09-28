from django.db import models
from django.core.urlresolvers import reverse
import datetime

from ..target.models import Target


class Project(models.Model):
    """
    A project represents the top level interpretation of the codebase to be
    tested. A project may have one or many Targets (build targets).
    """

    name = models.CharField(blank=False, max_length=100)
    name_slug = models.SlugField(blank=False, db_index=True, unique=True)
    url = models.CharField(blank=False, db_index=True, unique=True, max_length=255)
    description = models.TextField(blank=True)
    created_datetime = models.DateTimeField(blank=False, default=datetime.datetime.now)
    targets = models.ManyToManyField(Target)

    class Meta:
        pass

    def __unicode__(self):
        return u"%s" % (self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('project:show', (), {
            'project_name_slug':self.name_slug
        })
