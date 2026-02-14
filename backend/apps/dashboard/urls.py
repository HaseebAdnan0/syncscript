from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('recent-vaults/', views.recent_vaults, name='recent_vaults'),
    path('activity/', views.activity_feed, name='activity_feed'),
    path('analytics/sources-timeline/', views.sources_timeline, name='sources_timeline'),
    path('analytics/source-types/', views.source_types, name='source_types'),
    path('analytics/top-collaborators/', views.top_collaborators, name='top_collaborators'),
]
