from django.conf import settings
from django.conf.urls.defaults import *
from .views import project

urlpatterns = patterns('',
    url(r'^new/$', project.create, name='create'),
    url(r'^$', project.index, name='index'),
    url(r'^(?P<project_name_slug>[0-9A-Za-z-]+)/$', project.show, name='show'),
    url(r'^(?P<project_name_slug>[0-9A-Za-z-]+)/delete/$', project.delete, name='delete'),
)