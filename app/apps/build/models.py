from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
import datetime


class Build(models.Model):
    """(Project description)"""

    STATE_CHOICES = (
        ("a", "pending",),
        ("b", "running",),
        ("c", "pass",),
        ("d", "fail",),
    )
    project = models.ForeignKey('project.Project')
    project_name_slug = models.SlugField(blank=False, db_index=True, unique=False)

    state = models.CharField(blank=True, max_length=1, default="a", choices=STATE_CHOICES)
    created_datetime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    duration_ms = models.BigIntegerField(blank=True, null=True)
    log = models.TextField(blank=True)

    def __unicode__(self):
        return u"%s" % self.id

    def duration(self):
        return u"%.2f seconds" % (float(self.duration_ms) / float(1000000))

    def complete(self):
        return self.state in ('c', 'd')

    def build_steps(self):
        return self.step_set.filter(type='b')

    def setup_step(self):
        step = self.step_set.filter(type='a')
        if step:
            return step

    def teardown_step(self):
        step = self.step_set.filter(type='c')[0]
        if step:
            return step

    class Meta:
        ordering = ['-created_datetime']

    @models.permalink
    def get_absolute_url(self):
        # TODO: LOL, fix this!
        return ('build:show', (), {
            'build_id':self.id,
            'project_name_slug':self.project_name_slug
        })

    @models.permalink
    def get_stop_url(self):
        # TODO: LOL, fix this!
        return ('build:stop', (), {
            'build_id':self.id,
            'project_name_slug':self.project_name_slug
        })


class Step(models.Model):
    """Sup"""

    STATE_CHOICES = (
        ("a", "pending",),
        ("b", "running",),
        ("c", "pass",),
        ("d", "fail",),
    )

    TYPE_CHOICES = (
        ("a", "setup",),
        ("b", "build",),
        ("c", "teardown",)
    )

    build = models.ForeignKey(Build)
    type = models.CharField(blank=True, max_length=1, default="b", choices=TYPE_CHOICES)
    sha = models.CharField(blank=True, max_length=255)
    command = models.CharField(blank=False, max_length=255)
    created_datetime = models.DateTimeField(blank=True, default=datetime.datetime.now)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    log = models.TextField(blank=True)
    state = models.CharField(blank=True, max_length=1, default="a", choices=STATE_CHOICES)

    def __unicode__(self):
        return u"%s" % (self.command)

    def log_lines(self):
        return self.log.split("\n")

    class Meta:
        ordering = ['created_datetime']
