from django.urls import path
from . import views

urlpatterns = [
    # Source summarization (US-006)
    path('sources/<int:source_id>/summarize/', views.summarize_source, name='summarize-source'),
    # Vault insights (US-007)
    path('vaults/<uuid:vault_id>/insights/', views.vault_insights, name='vault-insights'),
]
