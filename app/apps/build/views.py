from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse


def show(request, build_id):
    """docstring for show"""
    
    build = get_object_or_404(Build, id=build_id)
    return render_to_response('project/build.html', {
        "build": build
    }, context_instance=RequestContext(request))