"""Serializers for annotations app"""
from rest_framework import serializers
from apps.annotations.models import Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation with nested replies"""
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Annotation
        fields = [
            'id',
            'source',
            'user',
            'content',
            'page_number',
            'position',
            'parent',
            'replies',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'replies']

    def get_replies(self, obj: Annotation) -> list:
        """Return nested replies for top-level annotations only (parent=None)"""
        # Only include replies for top-level annotations
        if obj.parent is None:
            # Serialize all replies to this annotation
            return AnnotationSerializer(obj.replies.all(), many=True, context=self.context).data
        # For reply-level annotations, don't include nested replies
        return []
