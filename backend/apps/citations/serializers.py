from rest_framework import serializers
from apps.citations.models import CitationFormat


class CitationRequestSerializer(serializers.Serializer):
    """Serializer for citation generation request"""
    format = serializers.ChoiceField(
        choices=CitationFormat.choices,
        required=True,
        help_text="Citation format to generate"
    )


class CitationResponseSerializer(serializers.Serializer):
    """Serializer for citation generation response"""
    citation = serializers.CharField(
        help_text="Plain text citation"
    )
    citation_html = serializers.CharField(
        help_text="HTML-formatted citation with italics"
    )
    format = serializers.ChoiceField(
        choices=CitationFormat.choices,
        help_text="Citation format used"
    )
    source = serializers.ChoiceField(
        choices=['structured', 'ai'],
        help_text="Generation method: structured (citeproc-py) or ai (Claude)"
    )
    cached = serializers.BooleanField(
        help_text="Whether citation was served from cache"
    )
