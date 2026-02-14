from django_filters import rest_framework as filters
from .models import Source


class SourceFilter(filters.FilterSet):
    """
    FilterSet for Source model with vault, type, creator, and date filters (US-012).
    """
    # Standard field filters
    vault = filters.UUIDFilter(field_name='vault')
    source_type = filters.CharFilter(field_name='source_type')
    created_by = filters.NumberFilter(field_name='created_by')

    # Date range filters
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Source
        fields = ['vault', 'source_type', 'created_by', 'date_from', 'date_to']
