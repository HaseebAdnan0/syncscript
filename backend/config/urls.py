"""
URL configuration for SyncScript project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.vaults.urls')),
    path('api/v1/sources/', include('apps.sources.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/citations/', include('apps.citations.urls')),
    path('api/v1/', include('apps.notifications.urls')),
]
