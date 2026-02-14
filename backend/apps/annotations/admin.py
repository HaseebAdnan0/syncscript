from django.contrib import admin
from .models import Annotation


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'user', 'truncated_content', 'parent', 'created_at']
    list_filter = ['source', 'user']
    search_fields = ['content']

    def truncated_content(self, obj: Annotation) -> str:
        """Display first 50 characters of content"""
        if len(obj.content) > 50:
            return obj.content[:50] + '...'
        return obj.content

    truncated_content.short_description = 'Content'  # type: ignore
