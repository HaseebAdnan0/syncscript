"""
URL routing for notifications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

# Main router for notifications
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
