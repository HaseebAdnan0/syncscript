from django_filters import rest_framework as filters
from .models import Source


class SourceFilter(filters.FilterSet):
    """
    FilterSet for Source model with vault, type, creator, date, and tag filters.
    """
    # Standard field filters
    vault = filters.UUIDFilter(field_name='vault')
    source_type = filters.CharFilter(field_name='source_type')
    created_by = filters.NumberFilter(field_name='created_by')

    # Date range filters
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    # Tags filter (US-013)
    tags = filters.CharFilter(method='filter_tags')

    class Meta:
        model = Source
        fields = ['vault', 'source_type', 'created_by', 'date_from', 'date_to', 'tags']

    def filter_tags(self, queryset, name, value):
        """
        Filter sources by tags stored in metadata['tags'] JSON array (US-013).
        Accepts comma-separated tags and returns sources with any of the specified tags.

        Example: ?tags=ml,nlp returns sources where metadata.tags contains 'ml' OR 'nlp'
        """
        if not value:
            return queryset

        # Split comma-separated tags and strip whitespace
        tag_list = [tag.strip() for tag in value.split(',') if tag.strip()]

        if not tag_list:
            return queryset

        # Use PostgreSQL metadata__tags__overlap lookup for array overlap
        # This checks if metadata['tags'] array overlaps with tag_list
        return queryset.filter(metadata__tags__overlap=tag_list)
