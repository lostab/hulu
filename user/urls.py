from django.conf.urls import patterns, url

from user import views

urlpatterns = patterns('',
    url(r'^$', views.Main, name='index'),
    url(r'^signup/$', views.Signup, name='signup'),
    url(r'^login/$', views.Login, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^settings/$', views.Settings, name='settings'),
    url(r'^notify/$', views.Notify, name='notify'),
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', name='password_change'),
    url(r'^password_change_done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', name='password_reset'),
    url(r'^password_reset_done/$', 'django.contrib.auth.views.password_reset_done', name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    #url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    url(r'^password_reset_complete/$', 'django.contrib.auth.views.password_reset_complete', name='password_reset_complete'),
    url(r'^feedback/$', views.Feedback, name='feedback'),
    url(r'^list/$', views.List, name='list'),
    #url(r'^m/$', views.MessageList, name='messagelist'),
    url(r'^m/(.+)/$', views.Message, name='message'),
)
