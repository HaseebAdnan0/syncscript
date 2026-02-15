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
# Register sources at root level (not nested under 'sources' again)
router.register(r'', SourceViewSet, basename='source')

# Nested router for source annotations (US-030)
# This creates routes like /sources/25/annotations/
from apps.annotations.views import AnnotationViewSet
sources_router = nested_routers.NestedDefaultRouter(router, r'', lookup='source')
sources_router.register(r'annotations', AnnotationViewSet, basename='source-annotations')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(sources_router.urls)),
]
