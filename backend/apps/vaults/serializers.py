"""
Serializers for vault RBAC system.
"""
from rest_framework import serializers
from .models import Vault, VaultMembership, AuditLog


class VaultSerializer(serializers.ModelSerializer):
    """
    Serializer for Vault API responses (US-009).
    Includes computed fields for member count and current user's role.
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Vault
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'is_archived', 'created_at', 'updated_at', 'member_count', 'user_role'
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
