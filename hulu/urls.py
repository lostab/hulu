from django.conf.urls import include, url

from django.contrib import admin
from user import views as user
from item import views as item
from main import views as main
from hulu import *

import settings
import os
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'hulu.views.main', name='main'),
    # url(r'^hulu/', include('hulu.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include('main.urls')),
    url(r'^a/login/', user.Login),
    url(r'^a/', include(admin.site.urls)),
    url(r'^u/', include('user.urls')),
    url(r'^i/', include('item.urls')),
    url(r'^t/', include('tag.urls')),
    url(r'^tg/', main.ttt, name='ttt'),
    url(r'^jk/(.+)/$', main.jk, name='jk'),
    url(r'^m/', main.app, name='app'),
    #url(r'^wi/', item.wbimg, name='wbimg'),
    #url(r'^wx/', main.weixin, name='weixin'),
    url(r'^cm/', main.coin, name='coin'),
    url(r'^(.+)/$', user.UserPage, name='userpage'),
    url(r'^a/sitemap.txt$', main.sitemap, name='sitemap'),
]

#urlpatterns += patterns('',
#    (r'^s/(.*)$', 'django.views.static.serve', {'document_root' :settings.STATIC_ROOT}),
#)

#urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()

if 'VCAP_SERVICES' in os.environ:
    urlpatterns += url(r'^s/avatar/(.+)$', user.Avatar, name='avatar'),
