"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
#from django.contrib.staticfiles import views
#from django.views.generic import TemplateView

urlpatterns = [
    path('',RedirectView.as_view(pattern_name='gerlumph_registration:login',permanent=False)),
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path('captcha/', include('captcha.urls')),
    path('users/', include('gerlumph_users.urls'), name='gerlumph_users'),
    path('accounts/', include('gerlumph_registration.urls'), name='gerlumph_registration'),
    path('limits/', include('gerlumph_limits.urls'), name='gerlumph_limits'),
    path('tasks/', include('gerlumph_tasks.urls'), name='gerlumph_tasks'),
    path('maps/', include('gerlumph_maps.urls'), name='gerlumph_maps'),
    path('downloads/', include('gerlumph_downloads.urls'), name='gerlumph_downloads'),
]

