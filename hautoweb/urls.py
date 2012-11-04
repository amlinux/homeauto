from django.conf.urls.defaults import *
from staticfiles.urls import urlpatterns as staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'hautoweb.portal.views.overview'),
    (r'^favicon\.ico$', 'staticfiles.views.serve', {"path": 'img/favicon.ico'}),
    (r'^homeauto/', include('hautoweb.portal.urls')),
#    (r'^$', 'hautoweb.mlansetup.views.index'),
    (r'^admin/', include(admin.site.urls)),
    (r'^media(?P<path>/.*)$', 'django.views.static.serve', {'document_root': admin.__path__[0] + "/media/"}),
    (r'^hwdebug/', include('hautoweb.hwdebug.urls')),
    (r'^api/', include('hautoweb.api.urls')),
)

urlpatterns += staticfiles_urlpatterns
