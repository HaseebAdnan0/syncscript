"""
Serializers for notification system.
"""
from rest_framework import serializers
from .models import Notification, NotificationPreferences, MutedVault


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification API responses (US-004, US-005).
    Includes computed is_read property for convenience.
    """
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'type', 'title', 'body', 'data',
            'read_at', 'created_at', 'is_read'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'read_at']

    def get_is_read(self, obj: Notification) -> bool:
        """
        Returns whether the notification has been read.
        Uses the model's is_read property.
        """
        return obj.is_read


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreferences API responses (US-004, US-009).
    Allows users to view and update their notification preferences.
    """

    class Meta:
        model = NotificationPreferences
        fields = [
            'id', 'user', 'email_vault_activity', 'email_mentions',
            'email_digest_frequency', 'push_enabled', 'push_sources',
            'push_annotations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_email_digest_frequency(self, value: str) -> str:
        """
        Validate email_digest_frequency is one of the allowed choices.
        """
        allowed_choices = [choice[0] for choice in NotificationPreferences.DIGEST_FREQUENCY_CHOICES]
        if value not in allowed_choices:
            raise serializers.ValidationError(
                f"Invalid frequency. Must be one of: {', '.join(allowed_choices)}"
            )
        return value


class MutedVaultSerializer(serializers.ModelSerializer):
    """
    Serializer for MutedVault API responses (US-004, US-010).
    Includes vault details (id, name) for display purposes.
    """
    vault_id = serializers.UUIDField(source='vault.id', read_only=True)
    vault_name = serializers.CharField(source='vault.name', read_only=True)

    class Meta:
        model = MutedVault
        fields = ['id', 'user', 'vault', 'vault_id', 'vault_name', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
