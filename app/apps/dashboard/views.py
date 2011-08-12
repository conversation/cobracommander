from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings

from ..project.models import Project
from ..build.models import Build



def show(request):
    """
    Dashboard show action
    """
    projects = Project.objects.all()
    return render_to_response('dashboard/show.html', {
        "projects": projects
    }, context_instance=RequestContext(request))