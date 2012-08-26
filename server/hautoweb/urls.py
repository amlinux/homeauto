from django.conf.urls.defaults import *
from staticfiles.urls import urlpatterns as staticfiles_urlpatterns

urlpatterns = patterns('',
    (r'^$', 'hautoweb.portal.views.overview'),
    (r'^favicon\.ico$', 'staticfiles.views.serve', {"path": 'img/favicon.ico'}),
    (r'^homeauto/', include('hautoweb.portal.urls')),
#    (r'^$', 'hautoweb.mlansetup.views.index'),
)

urlpatterns += staticfiles_urlpatterns
