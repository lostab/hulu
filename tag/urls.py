from django.conf.urls import patterns, url

from tag import views

urlpatterns = patterns('',
    url(r'^$', views.Index, name='index'),
    url(r'^create/$', views.Create, name='create'),
    url(r'^(?P<id>\d+)/$', views.View, name='task'),
    url(r'^update/(?P<id>\d+)/$', views.Update, name='update'),
    url(r'^cancel/(?P<id>\d+)/$', views.Cancel, name='cancel'),
)
