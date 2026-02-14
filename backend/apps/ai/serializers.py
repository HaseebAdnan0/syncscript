from rest_framework import serializers
from apps.sources.models import Source


class SummarizeRequestSerializer(serializers.Serializer):
    """
    Serializer for AI summary request parameters.
    """
    regenerate = serializers.BooleanField(default=False)


class SummarizeResponseSerializer(serializers.Serializer):
    """
    Serializer for AI summary response.
    Matches the expected schema from the ClaudeClient.
    """
    abstract = serializers.CharField()
    key_findings = serializers.ListField(child=serializers.CharField())
    methodology = serializers.CharField(allow_blank=True)
    limitations = serializers.CharField(allow_blank=True)
    keywords = serializers.ListField(child=serializers.CharField())
    language = serializers.CharField(default='en')
    quality_flags = serializers.ListField(child=serializers.CharField(), default=list)
    generated_at = serializers.DateTimeField()
