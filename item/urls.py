from django.conf.urls import url

from item import views

urlpatterns = [
    url(r'^$', views.Index, name='index'),
    url(r'^create/$', views.Create, name='create'),
    url(r'^(?P<id>\d+)/$', views.View, name='view'),
    url(r'^update/(?P<id>\d+)/$', views.Update, name='update'),
    url(r'^link/$', views.LinkClass, name='link'),
]
