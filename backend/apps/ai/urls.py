from django.urls import path
from . import views

urlpatterns = [
    # AI usage stats (US-023)
    path('ai/usage/', views.get_ai_usage, name='ai-usage'),
    # Source summarization (US-006)
    path('sources/<int:source_id>/summarize/', views.summarize_source, name='summarize-source'),
    # Vault insights (US-007)
    path('vaults/<uuid:vault_id>/insights/', views.vault_insights, name='vault-insights'),
    # Question answering (US-009)
    path('vaults/<uuid:vault_id>/ask/', views.ask_question, name='ask-question'),
    # Chat history (US-010)
    path('vaults/<uuid:vault_id>/conversations/', views.list_conversations, name='list-conversations'),
    path('vaults/<uuid:vault_id>/conversations/<int:conversation_id>/', views.get_conversation, name='get-conversation'),
]
