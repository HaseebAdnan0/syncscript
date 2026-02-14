"""
Serializers for dashboard API endpoints.
"""
from rest_framework import serializers
from apps.vaults.models import Vault, VaultMembership
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
