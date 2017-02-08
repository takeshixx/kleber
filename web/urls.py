from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.upload, name='index'),
    url(r'^about/$', views.about, name='about'),
    url(r'^cli/$', views.cli, name='cli'),
    url(r'^users/$', views.user_account, name='users_account'),
    url(r'^users/tokens/create/$', views.user_token_create, name='users_token_create'),
    url(r'^users/tokens/delete/(?P<token>[a-zA-Z0-9]+)/$', views.user_token_delete, name='users_token_delete'),
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
