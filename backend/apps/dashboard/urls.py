from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('recent-vaults/', views.recent_vaults, name='recent_vaults'),
]
