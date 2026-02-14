"""
Admin configuration for User model.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with email verification fields.
    """
    list_display = ['email', 'username', 'is_email_verified', 'institution', 'is_active', 'created_at']
    list_filter = ['is_email_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username', 'institution']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('bio', 'institution')
        }),
        ('Email Verification', {
            'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at')
        }),
    )

    readonly_fields = ['email_verification_sent_at', 'created_at', 'updated_at']

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'bio', 'institution')
        }),
    )
