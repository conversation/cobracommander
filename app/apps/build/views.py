from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from .models import Build
from ..project.models import Project

def show(request, project_name_slug, build_id):
    """docstring for show"""
    
    build = get_object_or_404(Build, id=build_id)
    return render_to_response('project/build/show.html', {
        "build": build
    }, context_instance=RequestContext(request))