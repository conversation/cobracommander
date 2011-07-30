import os
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^sentry/', include('sentry.web.urls')),
)

urlpatterns += patterns('',
    # url(r'account^', include('%s.app.apps.account.urls' % settings.PROJECT_MODULE, namespace='account')),
)

urlpatterns += staticfiles_urlpatterns()