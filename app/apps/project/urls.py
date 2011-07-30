from django.conf import settings
from django.conf.urls.defaults import *

from .views import *


urlpatterns = patterns('',
    url(r'^project/new/$', create, name='create'),
    url(r'^$', index, name='index'),
    url(r'^project/(?P<project_name_slug>[0-9A-Za-z-]+)/$', show, name='show'),
    url(r'^project/(?P<project_name_slug>[0-9A-Za-z-]+)/delete/$', delete, name='delete'),
)