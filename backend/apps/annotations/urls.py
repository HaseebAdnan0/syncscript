"""URL routing for annotations app"""
from rest_framework.routers import DefaultRouter
from apps.annotations.views import AnnotationViewSet

router = DefaultRouter()
router.register(r'annotations', AnnotationViewSet, basename='annotation')

urlpatterns = router.urls
