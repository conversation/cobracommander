from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
import json, string
import redis

from .models import Project
from .forms import ProjectForm
from ..target.models import Target
from ..build.models import Build


def index(request):
    """SUP BITCHES"""
    
    projects = Project.objects.all()
    build_queue = Build.objects.filter(state__in=['a','b'])
    return render_to_response('project/index.html', {
        "projects": projects,
        "build_queue": build_queue
    }, context_instance=RequestContext(request))


def create(request):
    """docstring for create"""
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request=request)
        if form.is_valid():
            project = form.save()
            return HttpResponseRedirect(reverse("project:config", kwargs={
                'project_name_slug':project.name_slug}) + "?first=true")
    else:
        form = ProjectForm(request=request)
    
    return render_to_response('project/create.html', {
        'form':form
    }, context_instance=RequestContext(request))


def show(request, project_name_slug):
    """docstring for show"""
    
    project = get_object_or_404(Project, name_slug=project_name_slug)
    targets = Target.objects.filter(project=project)
    return render_to_response('project/show.html', {
        "project": project,
        "targets": targets
    }, context_instance=RequestContext(request))


def config(request, project_name_slug):
    """docstring for config"""
    
    project = get_object_or_404(Project, name_slug=project_name_slug)

    first_time = request.GET.get('first', False)
    build_templates = {
        "django": "I am a Django man",
        "rails": "Rails is my poison"
    }
    
    return render_to_response('project/config.html', {
        "project": project,
        "build_templates": build_templates,
        "first_time": first_time
    }, context_instance=RequestContext(request))


def delete(request, project_name_slug):
    """docstring for delete"""
    return