"""
URL routing for sources app (PDF uploads, sources, annotations).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PDFUploadViewSet, SourceViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'pdfs', PDFUploadViewSet, basename='pdf-upload')
router.register(r'sources', SourceViewSet, basename='source')

urlpatterns = [
    path('', include(router.urls)),
]
