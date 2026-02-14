from django.urls import path
from . import views

urlpatterns = [
    # Source summarization (US-006)
    path('sources/<int:source_id>/summarize/', views.summarize_source, name='summarize-source'),
]
