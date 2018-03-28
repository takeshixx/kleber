from django.conf.urls import url
from django.http import HttpResponse

from . import views


urlpatterns = [
    url(r'^$', views.upload, name='index'),
    url(r'^about/?$', views.about, name='about'),
    url(r'^cli/?$', views.cli, name='cli'),
    url(r'^robots.txt', lambda x: HttpResponse("User-Agent: *\nDisallow:", content_type="text/plain"), name="robots_file"),
    url(r'^users/?$', views.user_account, name='users_account'),
    url(r'^users/tokens/create/$', views.user_token_create, name='users_token_create'),
    url(r'^users/tokens/delete/(?P<token>[a-zA-Z0-9]+)/$', views.user_token_delete, name='users_token_delete'),
    url(r'^users/vouchers/create/$', views.user_voucher_create, name='users_voucher_create'),
    url(r'^users/vouchers/delete/(?P<code>[a-fA-F0-9]+)/$', views.user_voucher_delete, name='users_voucher_delete'),
    url(r'^uploads/new$', views.upload, name='upload'),
    url(r'^uploads/new/(?P<shortcut>[a-zA-Z0-9]+)$', views.upload, name='upload_repaste'),
    url(r'^uploads/$', views.get_uploads, name='upload_history'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9-_]+)$', views.get_uploads, name='uploads'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9-_]+)/delete$', views.delete, name='delete'),
    url(r'^uploads/(?P<shortcut>[a-zA-Z0-9-_]+)/$', views.uploads_plain, name='uploads_plain'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9-_]+)$', views.get_uploads, name='uploads_short'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9]-_+)/delete$', views.delete, name='uploads_delete_short'),
    url(r'^(?P<shortcut>(?!admin)[a-zA-Z0-9-_]+)/$', views.uploads_plain, name='uploads_plain_short')
]
