from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.citations.views import CitationViewSet  # type: ignore[import-untyped]
from apps.citations.export_views import export_vault_citations, export_status, export_download  # type: ignore[import-untyped]

app_name = 'citations'

router = DefaultRouter()
router.register(r'', CitationViewSet, basename='citation')

urlpatterns = [
    # Batch export endpoints
    path('vaults/<uuid:vault_id>/export/', export_vault_citations, name='vault-export'),
    path('export/status/<str:task_id>/', export_status, name='export-status'),
    path('export/download/<str:cache_key>/', export_download, name='export-download'),
    path('', include(router.urls)),
]
