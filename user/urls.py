from django.conf.urls import url

from user import views
from django.contrib.auth import views as authviews

urlpatterns = [
    url(r'^$', views.Main, name='index'),
    url(r'^signup/$', views.Signup, name='signup'),
    url(r'^login/$', views.Login, name='login'),
    url(r'^logout/$', authviews.logout, {'next_page': '/'}, name='logout'),
    url(r'^settings/$', views.Settings, name='settings'),
    url(r'^notify/$', views.Notify, name='notify'),
    url(r'^password_change/$', authviews.password_change, name='password_change'),
    url(r'^password_change_done/$', authviews.password_change_done, name='password_change_done'),
    url(r'^password_reset/$', authviews.password_reset, name='password_reset'),
    url(r'^password_reset_done/$', authviews.password_reset_done, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', authviews.password_reset_confirm, name='password_reset_confirm'),
    #url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    url(r'^password_reset_complete/$', authviews.password_reset_complete, name='password_reset_complete'),
    url(r'^feedback/$', views.Feedback, name='feedback'),
    url(r'^list/$', views.List, name='list'),
]
