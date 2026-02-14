"""
Serializers for dashboard API endpoints.
"""
from rest_framework import serializers
from apps.vaults.models import Vault, VaultMembership, AuditLog
from apps.sources.models import Source


class RecentVaultSerializer(serializers.ModelSerializer):
    """
    Serializer for recent vaults in dashboard.
    Includes last_accessed_at, sources_count, and user's role.
    """
    last_accessed_at = serializers.SerializerMethodField()
    sources_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Vault
        fields = ['id', 'name', 'description', 'last_accessed_at', 'sources_count', 'role']

    def get_last_accessed_at(self, obj):
        """
        Returns the last_accessed_at timestamp from membership, or updated_at as fallback.
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return obj.updated_at

        membership = obj.memberships.filter(user=request.user).first()
        if membership and membership.last_accessed_at:
            return membership.last_accessed_at
        return obj.updated_at

    def get_sources_count(self, obj):
        """
        Returns the count of non-deleted sources in this vault.
        """
        return Source.objects.filter(vault=obj, is_deleted=False).count()

    def get_role(self, obj):
        """
        Returns the current user's role in this vault.
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None

        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None


class ActivityFeedSerializer(serializers.ModelSerializer):
    """
    Serializer for activity feed items from AuditLog.
    Provides human-readable descriptions of actions across vaults.
    """
    actor = serializers.SerializerMethodField()
    vault_name = serializers.CharField(source='vault.name', read_only=True)
    vault_id = serializers.UUIDField(source='vault.id', read_only=True)
    description = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'description',
            'actor',
            'vault_id',
            'vault_name',
            'target_type',
            'target_id',
            'created_at'
        ]

    def get_actor(self, obj):
        """
        Returns actor information (user who performed the action).
        """
        if not obj.actor:
            return None
        return {
            'id': obj.actor.id,
            'username': obj.actor.username,
            'email': obj.actor.email,
            'first_name': obj.actor.first_name,
            'last_name': obj.actor.last_name,
        }

    def get_description(self, obj):
        """
        Formats action as human-readable description.
        Examples:
        - "added source 'Research Paper'"
        - "created annotation on 'Study Results'"
        - "invited user@example.com to vault"
        """
        action = obj.action.lower()
        metadata = obj.metadata or {}

        # Extract common metadata fields
        title = metadata.get('title', '')
        name = metadata.get('name', '')
        email = metadata.get('email', '')

        # Format description based on action type
        if 'source' in action:
            if 'create' in action or 'add' in action:
                return f"added source '{title}'" if title else "added a source"
            elif 'update' in action or 'edit' in action:
                return f"updated source '{title}'" if title else "updated a source"
            elif 'delete' in action or 'remove' in action:
                return f"removed source '{title}'" if title else "removed a source"

        elif 'annotation' in action:
            if 'create' in action or 'add' in action:
                return f"created annotation on '{title}'" if title else "created an annotation"
            elif 'update' in action or 'edit' in action:
                return f"updated annotation on '{title}'" if title else "updated an annotation"
            elif 'delete' in action or 'remove' in action:
                return f"removed annotation from '{title}'" if title else "removed an annotation"

        elif 'member' in action or 'invite' in action:
            if 'add' in action or 'invite' in action:
                return f"invited {email} to vault" if email else "invited a collaborator"
            elif 'remove' in action:
                return f"removed {email} from vault" if email else "removed a collaborator"
            elif 'update' in action:
                return f"updated role for {email}" if email else "updated a member's role"

        elif 'vault' in action:
            if 'create' in action:
                return f"created vault '{name}'" if name else "created a vault"
            elif 'update' in action or 'edit' in action:
                return f"updated vault '{name}'" if name else "updated vault settings"
            elif 'archive' in action:
                return f"archived vault '{name}'" if name else "archived the vault"

        # Default fallback
        return obj.action.replace('_', ' ').capitalize()

    def get_target_type(self, obj):
        """
        Returns the type of entity affected (source, annotation, member, vault).
        """
        action = obj.action.lower()
        if 'source' in action:
            return 'source'
        elif 'annotation' in action:
            return 'annotation'
        elif 'member' in action or 'invite' in action:
            return 'member'
        elif 'vault' in action:
            return 'vault'
        return None

    def get_target_id(self, obj):
        """
        Returns the ID of the affected entity if available in metadata.
        """
        metadata = obj.metadata or {}
        return metadata.get('target_id') or metadata.get('source_id') or metadata.get('annotation_id')
