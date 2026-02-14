from django.contrib import admin
from .models import Notification, NotificationPreferences


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'read_at', 'created_at']
    search_fields = ['user__username', 'title', 'body']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_digest_frequency', 'push_enabled', 'updated_at']
    list_filter = ['email_digest_frequency', 'push_enabled', 'email_vault_activity', 'email_mentions']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
