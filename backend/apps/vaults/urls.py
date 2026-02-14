"""
URL routing for vaults app with nested routes.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import VaultViewSet, VaultMembershipViewSet, AuditLogViewSet

# Main router for vaults
router = DefaultRouter()
router.register(r'vaults', VaultViewSet, basename='vault')

# Nested router for vault members
vaults_router = nested_routers.NestedDefaultRouter(router, r'vaults', lookup='vault')
vaults_router.register(r'members', VaultMembershipViewSet, basename='vault-members')
vaults_router.register(r'audit-logs', AuditLogViewSet, basename='vault-audit-logs')

# Nested router for vault sources (defined in sources app but registered here)
from apps.sources.views import SourceViewSet, PDFUploadViewSet
vaults_router.register(r'sources', SourceViewSet, basename='vault-sources')

# Nested router for vault PDFs (US-023)
vaults_router.register(r'pdfs', PDFUploadViewSet, basename='vault-pdfs')

# Import citation export view
from apps.citations.export_views import export_vault_citations

urlpatterns = [
    # Citation export endpoint (function-based view to avoid routing issues)
    # IMPORTANT: Must be BEFORE router includes to avoid being shadowed
    path('vaults/<uuid:vault_id>/citations/export/', export_vault_citations, name='vault-export-citations-func'),
    path('', include(router.urls)),
    path('', include(vaults_router.urls)),
]
