from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^demo/$', 'hautoweb.hwdebug.views.demo'),
)
