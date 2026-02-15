"""
URL configuration for SyncScript project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint for Docker/load balancer."""
    return JsonResponse({'status': 'healthy', 'service': 'syncscript'})


urlpatterns = [
    path('api/v1/health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.vaults.urls')),
    path('api/v1/sources/', include('apps.sources.urls')),
    path('api/v1/', include('apps.annotations.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/citations/', include('apps.citations.urls')),
    path('api/v1/', include('apps.notifications.urls')),
    path('api/v1/', include('apps.ai.urls')),
    path('api/v1/search/', include('apps.search.urls')),
    # django-allauth URLs for OAuth callbacks
    path('api/v1/auth/', include('allauth.urls')),
]
