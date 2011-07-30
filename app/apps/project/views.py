from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from .models import Project
from .forms import ProjectForm


def index(request):
  """SUP BITCHES"""
  
  projects = Project.objects.all()
  return render_to_response('project/index.html', {
    "projects": projects
  }, context_instance=RequestContext(request))

def create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request=request)
        if form.is_valid():
            project = form.save()
            return HttpResponseRedirect(reverse("project:config", kwargs={'project_name_slug':project.name_slug}))
    else:
        form = ProjectForm(request=request)
    
    return render_to_response('project/create.html', {
        'form':form
    }, context_instance=RequestContext(request))

def show(request, project_name_slug):
  project = get_object_or_404(Project, name_slug=project_name_slug)
  return render_to_response('project/show.html', {
    "project": project
  }, context_instance=RequestContext(request))
  return

def config(request, project_name_slug):
  project = get_object_or_404(Project, name_slug=project_name_slug)
  
  build_templates = {
    "django": "I am a Django man",
    "rails": "Rails is my poison"
  }
  
  return render_to_response('project/config.html', {
    "project": project,
    "build_templates": build_templates
  }, context_instance=RequestContext(request))
  return


def new(request):
  return

def delete(request, project_name_slug):
  return