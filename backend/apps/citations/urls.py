from django.urls import path
from apps.citations.views import CitationViewSet  # type: ignore[import-untyped]
from apps.citations.export_views import export_vault_citations, export_status, export_download  # type: ignore[import-untyped]

app_name = 'citations'

# Get the custom actions from CitationViewSet
citation_viewset = CitationViewSet.as_view({
    'get': 'task_status',
})
generate_citation_view = CitationViewSet.as_view({
    'post': 'generate_citation',
})

urlpatterns = [
    # Batch export endpoints (explicit paths take priority)
    path('vaults/<uuid:vault_id>/export/', export_vault_citations, name='vault-export'),
    path('export/status/<str:task_id>/', export_status, name='export-status'),
    path('export/download/<str:cache_key>/', export_download, name='export-download'),
    # Citation generation endpoints (from ViewSet actions)
    path('sources/<int:source_id>/citation/', generate_citation_view, name='generate-citation'),
    path('tasks/<str:task_id>/', citation_viewset, name='task-status'),
]
