from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('suggestions/', views.suggestions_view, name='suggestions'),
    path('recent/', views.recent_searches_view, name='recent_searches'),
    path('recent/<int:search_id>/', views.delete_recent_search_view, name='delete_recent_search'),
]
