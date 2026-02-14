"""Filters for annotations app"""
from django_filters import rest_framework as filters
from apps.annotations.models import Annotation


class AnnotationFilter(filters.FilterSet):
    """
    Filter for Annotation model (US-032).
    Allows filtering by user and page_number.
    """
    user = filters.NumberFilter(field_name='user')
    page_number = filters.NumberFilter(field_name='page_number')

    class Meta:
        model = Annotation
        fields = ['user', 'page_number']
