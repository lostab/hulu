from django.conf.urls import patterns, include, url

from user import views as user
from main import views as main

import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'hulu.views.main', name='main'),
    # url(r'^hulu/', include('hulu.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include('main.urls')),
    url(r'^u/', include('user.urls')),
    url(r'^i/', include('item.urls')),
    url(r'^tg/', main.ttt, name='ttt'),
    url(r'^sq/', main.sq, name='sq'),
    url(r'^(.+)/$', user.UserPage, name='userpage'),
)

#urlpatterns += patterns('',
#(r'^s/(.*)$', 'django.views.static.serve', {'document_root' :settings.STATIC_ROOT}),
#)
