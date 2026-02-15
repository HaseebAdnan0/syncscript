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

    def create(self, validated_data):
        """Handle create with field mapping"""
        # Map camelCase fields back to snake_case for model
        if 'content' not in validated_data and 'text' in self.initial_data:
            validated_data['content'] = self.initial_data['text']
        if 'page_number' not in validated_data and 'pageNumber' in self.initial_data:
            validated_data['page_number'] = self.initial_data['pageNumber']
        return super().create(validated_data)
