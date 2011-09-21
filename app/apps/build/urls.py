from django.conf import settings
from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^project/(?P<project_name_slug>[0-9A-Za-z-]+)/build/(?P<build_id>[0-9]+)/$', show, name='show'),
    url(r'^project/(?P<project_name_slug>[0-9A-Za-z-]+)/build/(?P<build_id>[0-9]+)/stop/$', show, name='stop'),
)
