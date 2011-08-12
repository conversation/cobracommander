import os
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
	url(r'^', include('%s.app.apps.dashboard.urls' % settings.PROJECT_MODULE, namespace='dashboard')),
    url(r'^', include('%s.app.apps.project.urls' % settings.PROJECT_MODULE, namespace='project')),
    url(r'^', include('%s.app.apps.build.urls' % settings.PROJECT_MODULE, namespace='build')),
)

urlpatterns += staticfiles_urlpatterns()