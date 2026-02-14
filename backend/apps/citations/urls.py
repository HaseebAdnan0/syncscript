from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.citations.views import CitationViewSet
from apps.citations.export_views import export_vault_citations

app_name = 'citations'

router = DefaultRouter()
router.register(r'', CitationViewSet, basename='citation')

urlpatterns = [
    # Batch export endpoint - placed here to avoid router conflicts with /vaults/ URLs
    # Access via: GET /api/v1/citations/vaults/{vault_id}/export/?format=apa7
    path('vaults/<uuid:vault_id>/export/', export_vault_citations, name='vault-export'),
    path('', include(router.urls)),
]
