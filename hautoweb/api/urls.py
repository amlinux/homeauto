from django.conf.urls.defaults import *

urlpatterns = patterns('hautoweb.api.views',
    (r'^login$', 'loginView'),
    (r'^monitor$', 'monitor'),
)
