"""Serializers for annotations app"""
from rest_framework import serializers
from apps.annotations.models import Annotation


class AuthorSerializer(serializers.Serializer):
    """Serializer for annotation author info"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation with nested replies"""
    author = serializers.SerializerMethodField(read_only=True)
    text = serializers.CharField(source='content')
    pageNumber = serializers.IntegerField(source='page_number', allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Annotation
        fields = [
            'id',
            'source',
            'author',
            'text',
            'pageNumber',
            'position',
            'parent',
            'replies',
            'createdAt',
            'updatedAt'
        ]
        read_only_fields = ['author', 'createdAt', 'updatedAt', 'replies']

    def get_author(self, obj: Annotation) -> dict:
        """Return author as an object with id, username, email"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username or obj.user.email.split('@')[0],
                'email': obj.user.email,
            }
        return None

    def get_replies(self, obj: Annotation) -> list:
        """Return nested replies for top-level annotations only (parent=None)"""
        # Only include replies for top-level annotations
        if obj.parent is None:
            # Serialize all replies to this annotation
            return AnnotationSerializer(obj.replies.all(), many=True, context=self.context).data
        # For reply-level annotations, don't include nested replies
        return []

    def validate(self, attrs):
        """Validate that replies cannot be nested more than 2 levels"""
        parent = attrs.get('parent')
        if parent and parent.parent:
            raise serializers.ValidationError("Cannot reply to a reply (max 2 levels).")
        return attrs

    def update(self, instance, validated_data):
        """Handle update with immutable field protection"""
        # Remove immutable fields if present in validated_data
        validated_data.pop('source', None)
        validated_data.pop('position', None)
        validated_data.pop('parent', None)
        return super().update(instance, validated_data)
