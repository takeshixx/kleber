"""kleber URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from api import views as api_views

api_router = routers.SimpleRouter()
api_router.register(r'pastes', api_views.PasteViewSet, 'pastes')
api_router.register(r'files', api_views.FileViewSet, 'files')
api_router.register(r'uploads', api_views.UploadViewSet, 'uploads')

urlpatterns = [
    url(r'^accounts/', include('allauth.urls')),
    url(r'^api/', include(api_router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^klebercontrolpanel/?', admin.site.urls),
    url(r'^', include('web.urls')),
]

if settings.DEBUG == False:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
