"""
Serializers for vault RBAC system.
"""
from rest_framework import serializers
from .models import Vault, VaultMembership, AuditLog


class VaultSerializer(serializers.ModelSerializer):
    """
    Serializer for Vault API responses (US-009, US-015).
    Includes computed fields for member count, current user's role, and storage usage.
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    storage_used_bytes = serializers.SerializerMethodField()
    storage_file_count = serializers.SerializerMethodField()
    storage_user_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Vault
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'is_archived', 'created_at', 'updated_at', 'member_count', 'user_role',
            'storage_used_bytes', 'storage_file_count', 'storage_user_breakdown'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        """
        Returns the total number of members in this vault.
        """
        return obj.members.count()

    def get_user_role(self, obj):
        """
        Returns the current user's role in this vault, or None if not a member.
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None

        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None

    def get_storage_used_bytes(self, obj):
        """
        Returns the total storage used by this vault in bytes.
        Returns 0 if VaultStorageUsage record doesn't exist.
        """
        try:
            return obj.storage_usage.total_bytes
        except Exception:
            return 0

    def get_storage_file_count(self, obj):
        """
        Returns the number of files in this vault.
        Returns 0 if VaultStorageUsage record doesn't exist.
        """
        try:
            return obj.storage_usage.file_count
        except Exception:
            return 0

    def get_storage_user_breakdown(self, obj):
        """
        Returns the per-user storage breakdown as a JSON dict.
        Returns empty dict if VaultStorageUsage record doesn't exist.
        """
        try:
            return obj.storage_usage.user_breakdown
        except Exception:
            return {}


class VaultMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for VaultMembership API responses (US-010).
    Includes user details (username, email) for member listings.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VaultMembership
        fields = [
            'id', 'user', 'username', 'email', 'role', 'added_at', 'added_by'
        ]
        read_only_fields = ['id', 'added_at', 'added_by']


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog API responses (US-011).
    All fields are read-only since audit logs are immutable.
    """

    class Meta:
        model = AuditLog
        fields = ['id', 'vault', 'actor', 'action', 'metadata', 'created_at']
        read_only_fields = ['id', 'vault', 'actor', 'action', 'metadata', 'created_at']
