from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from .models import Project

def index(request):
  """SUP BITCHES"""
  
  projects = Project.objects.all()
  return render_to_response('project/index.html', {
    # Stuff
  }, context_instance=RequestContext(request))

def create(request):
  projects = Project.objects.all()
  return render_to_response('project/index.html', {
    # Stuff
  }, context_instance=RequestContext(request))

def show(request, project_name_slug):
  return

def new(request):
  return

def delete(request, project_name_slug):
  return