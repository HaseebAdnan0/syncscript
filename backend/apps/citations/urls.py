from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.citations.views import CitationViewSet

app_name = 'citations'

router = DefaultRouter()
router.register(r'', CitationViewSet, basename='citation')

urlpatterns = [
    path('', include(router.urls)),
]
