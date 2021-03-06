# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from phoenix.dashboard.views import DashboardView
from django.views.generic import RedirectView
from phoenix.users.views import LoginView

urlpatterns = [#url(r'^$', DashboardView.as_view(), name='dashboard'),
               url(r'^$', RedirectView.as_view(pattern_name='animals.animal_list'), name='dashboard'),
               url(r'^records/', include('phoenix.records.urls')),
               url(r'^health/', include('phoenix.health.urls')),
               url(r'^animals/', include('phoenix.animals.urls')),
               url(r'^groups/', include('phoenix.groups.urls')),
               # Django Admin
               url(r'^grappelli/', include('grappelli.urls')),
               url(r'^admin/', include(admin.site.urls)),
               # User management
               url(r'^accounts/', include('allauth.urls')),
               url(r'^users/', include('phoenix.users.urls', namespace="users")),
               url(r'^login/$', LoginView.as_view(), name='user_login'),
               # Third party URLs
               url(r'^select2/', include('django_select2.urls')),
               ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', 'django.views.defaults.bad_request'),
        url(r'^403/$', 'django.views.defaults.permission_denied'),
        url(r'^404/$', 'django.views.defaults.page_not_found'),
        url(r'^500/$', 'django.views.defaults.server_error'),
    ]
