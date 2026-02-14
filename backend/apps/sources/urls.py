"""
URL routing for sources app (PDF uploads, sources, annotations).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PDFUploadViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'pdfs', PDFUploadViewSet, basename='pdf-upload')

urlpatterns = [
    path('', include(router.urls)),
]
