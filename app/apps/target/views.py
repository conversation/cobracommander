from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
import json, string
import redis

from .models import Target
from ..project.models import Project
from ..build.models import Build


def build(request, project_name_slug, branch):
    """docstring for build"""
    project = get_object_or_404(Project, name_slug=project_name_slug)
    target = project.targets.get(branch=branch)

    if request.method == 'POST':
      build = Build(project=project, project_name_slug=project.name_slug)
      build.save()
      target.builds.add(build)
      target.save()
      build_queue = redis.Redis(**settings.REDIS_DATABASE)
      build_queue.rpush('build_queue', build.id)
      return HttpResponseRedirect(build.get_absolute_url())
    raise Http404
