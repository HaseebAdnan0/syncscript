from django.contrib import admin
from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'vault', 'source_type', 'is_deleted', 'created_at']
    list_filter = ['source_type', 'is_deleted']
    search_fields = ['title', 'url']
