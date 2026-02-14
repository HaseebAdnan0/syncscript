from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'read_at', 'created_at']
    search_fields = ['user__username', 'title', 'body']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
