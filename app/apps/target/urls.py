from django.conf import settings
from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^project/(?P<project_name_slug>[0-9A-Za-z-]+)/(?P<branch>[0-9A-Za-z-]+)/build/$', build, name='build'),
)