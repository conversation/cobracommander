from django.conf import settings
from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^projects/(?P<project_name_slug>[0-9A-Za-z-]+)/ref/(?P<ref>[0-9A-Za-z]+)/$', show, name='show'),
)