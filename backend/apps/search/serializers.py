from rest_framework import serializers
from .models import SearchHistory


class SearchResultSerializer(serializers.Serializer):
    """
    Serializer for search results (US-008).
    Represents a single search result item with highlighting and metadata.
    """
    id = serializers.UUIDField(help_text="ID of the vault/source/annotation")
    type = serializers.ChoiceField(
        choices=['vault', 'source', 'annotation'],
        help_text="Type of search result"
    )
    title = serializers.CharField(help_text="Title or name of the result")
    snippet = serializers.CharField(
        allow_blank=True,
        help_text="Text snippet from the content"
    )
    highlight = serializers.CharField(
        allow_blank=True,
        help_text="Highlighted matching text with <mark> tags"
    )
    relevance = serializers.FloatField(
        help_text="Relevance score from PostgreSQL search rank"
    )
    vault_id = serializers.UUIDField(
        allow_null=True,
        help_text="ID of the parent vault"
    )
    vault_name = serializers.CharField(
        allow_blank=True,
        help_text="Name of the parent vault"
    )
    breadcrumb = serializers.CharField(
        allow_blank=True,
        help_text="Breadcrumb trail for context (e.g., 'Vault Name > Source Title')"
    )


class SearchHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for SearchHistory model (US-008).
    Used for listing and managing user search history.
    """
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'result_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class SearchSuggestionSerializer(serializers.Serializer):
    """
    Serializer for search suggestions (US-008).
    Provides typeahead suggestions based on existing content.
    """
    text = serializers.CharField(help_text="Suggested search text")
    type = serializers.ChoiceField(
        choices=['source', 'annotation', 'vault'],
        help_text="Type of content this suggestion came from"
    )
    count = serializers.IntegerField(
        help_text="Number of matches for this suggestion"
    )
