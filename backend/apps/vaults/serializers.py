"""
Serializers for vault RBAC system.
"""
from rest_framework import serializers
from django.conf import settings
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
    storage_usage = serializers.SerializerMethodField()

    class Meta:
        model = Vault
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'is_archived', 'created_at', 'updated_at', 'member_count', 'user_role',
            'storage_used_bytes', 'storage_file_count', 'storage_user_breakdown',
            'storage_usage', 'default_citation_format'
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

    def get_storage_usage(self, obj):
        """
        Returns complete storage quota information for the vault.
        Includes: used_bytes, limit_bytes, percentage, warning, file_count
        """
        from apps.sources.models import VaultStorageUsage

        # Get or create storage usage record
        storage_usage, _ = VaultStorageUsage.objects.get_or_create(
            vault_id=obj.id,
            defaults={'total_bytes': 0, 'file_count': 0}
        )

        used_bytes = storage_usage.total_bytes
        limit_bytes = settings.VAULT_STORAGE_LIMIT
        file_count = storage_usage.file_count

        # Calculate percentage (can exceed 1.0)
        percentage = used_bytes / limit_bytes if limit_bytes > 0 else 0.0

        # Determine warning state
        warning_threshold = settings.VAULT_STORAGE_WARNING_THRESHOLD
        warning = percentage >= warning_threshold

        return {
            'used_bytes': used_bytes,
            'limit_bytes': limit_bytes,
            'percentage': percentage,
            'warning': warning,
            'file_count': file_count,
        }


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

    def validate(self, attrs):
        """
        Validate ownership transfer and last owner protection (US-033, US-034).
        - Prevents downgrading/removing the last owner
        - Validates single OWNER constraint (automatic demotion happens in update())
        """
        from .models import RoleChoices

        # Get the vault (from instance for updates, from attrs for creates)
        vault = self.instance.vault if self.instance else attrs.get('vault')
        role = attrs.get('role', self.instance.role if self.instance else None)

        # US-034: Validate ownership transfer - member must already exist
        if role == RoleChoices.OWNER and self.instance:
            # Validate user is already a member (updating existing membership)
            # This is inherently satisfied if self.instance exists
            pass

        # US-033: Last owner protection - only validate on updates
        if self.instance:
            # Check if this is the last owner being downgraded
            if self.instance.role == RoleChoices.OWNER and role != RoleChoices.OWNER:
                # Count how many owners exist in this vault
                owner_count = VaultMembership.objects.filter(
                    vault=vault,
                    role=RoleChoices.OWNER
                ).count()

                if owner_count <= 1:
                    raise serializers.ValidationError(
                        "Vault must have at least one owner"
                    )

        return attrs

    def update(self, instance, validated_data):
        """
        Handle ownership transfer (US-034).
        When promoting a member to OWNER, automatically demote the existing owner to CONTRIBUTOR.
        """
        from .models import RoleChoices

        role = validated_data.get('role', instance.role)

        # US-034: Automatic ownership transfer
        if role == RoleChoices.OWNER and instance.role != RoleChoices.OWNER:
            # Find and demote the existing owner
            existing_owner = VaultMembership.objects.filter(
                vault=instance.vault,
                role=RoleChoices.OWNER
            ).exclude(pk=instance.pk).first()

            if existing_owner:
                existing_owner.role = RoleChoices.CONTRIBUTOR
                existing_owner.save()

        return super().update(instance, validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog API responses (US-011).
    All fields are read-only since audit logs are immutable.
    """

    class Meta:
        model = AuditLog
        fields = ['id', 'vault', 'actor', 'action', 'metadata', 'created_at']
        read_only_fields = ['id', 'vault', 'actor', 'action', 'metadata', 'created_at']
