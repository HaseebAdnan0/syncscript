from django.contrib import admin
from .models import Vault, VaultMembership, AuditLog


@admin.register(Vault)
class VaultAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'is_archived', 'created_at']


@admin.register(VaultMembership)
class VaultMembershipAdmin(admin.ModelAdmin):
    list_display = ['vault', 'user', 'role', 'added_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['vault', 'actor', 'action', 'created_at']
