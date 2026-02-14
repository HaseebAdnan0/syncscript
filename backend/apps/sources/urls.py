"""
URL routing for sources app (PDF uploads, sources, annotations).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import PDFUploadViewSet, SourceViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'pdfs', PDFUploadViewSet, basename='pdf-upload')
router.register(r'sources', SourceViewSet, basename='source')

# Nested router for source annotations (US-030)
from apps.annotations.views import AnnotationViewSet
sources_router = nested_routers.NestedDefaultRouter(router, r'sources', lookup='source')
sources_router.register(r'annotations', AnnotationViewSet, basename='source-annotations')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(sources_router.urls)),
]
