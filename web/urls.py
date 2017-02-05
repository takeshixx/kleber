from django.conf.urls import url, include

from . import views


urlpatterns = [
    url(r'^$', views.upload, name='index'),
    url(r'^about/$', views.about, name='about'),
    url(r'^cli/$', views.cli, name='cli'),
    url(r'^register/$', views.user_register, name='users_register'),
    url(r'^login/$', views.user_login, name='users_login'),
    url(r'^logout/$', views.user_logout, name='users_logout'),
    url(r'^users/$', views.user_account, name='users_account'),
    url(r'^users/pwreset/$', views.users_pwreset, name='users_pwreset'),
    url(r'^users/pwchange/$', views.users_pwchange, name='users_pwchange'),
    url(r'^users/change/$', views.users_userchange, name='users_userchange'),
    url(r'^uploads/new$', views.upload, name='upload'),
    url(r'^uploads/new/(?P<shortcut>[a-zA-Z0-9]+)$', views.upload, name='upload_repaste'),
    url(r'^uploads/$', views.get_uploads, name='upload_history'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9]+)$', views.get_uploads, name='uploads'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9]+)/delete$', views.delete, name='delete'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9]+)/$', views.uploads_plain, name='uploads_plain'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9]+)$', views.get_uploads, name='uploads_short'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9]+)/delete$', views.delete, name='uploads_delete_short'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9]+)/$', views.uploads_plain, name='uploads_plain_short')
]
