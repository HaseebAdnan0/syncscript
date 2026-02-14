"""
Django signals for citation cache invalidation.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.sources.models import Source
from apps.citations.utils import invalidate_citation_cache


@receiver(pre_save, sender=Source)
def invalidate_cache_on_metadata_change(sender, instance, **kwargs):
    """
    Invalidate citation cache when source metadata is updated.

    This signal triggers before a Source instance is saved.
    If the metadata field has changed, we invalidate all cached citations
    to ensure they are regenerated with the new metadata.

    Args:
        sender: Source model class
        instance: Source instance being saved
        **kwargs: Signal kwargs (raw, using, update_fields)
    """
    # Skip for new sources (no pk yet)
    if not instance.pk:
        return

    # Skip if this is a raw save (e.g., fixtures)
    if kwargs.get('raw', False):
        return

    # Check if metadata field is dirty (changed)
    # DirtyFieldsMixin provides is_dirty() and get_dirty_fields()
    if instance.is_dirty(check_relationship=False):
        dirty_fields = instance.get_dirty_fields()

        # If metadata has changed, invalidate citation cache
        if 'metadata' in dirty_fields:
            # We need to invalidate before save completes
            # But we can't modify instance.metadata here without causing recursion
            # So we'll check if citations exist and remove them
            if instance.metadata and 'citations' in instance.metadata:
                del instance.metadata['citations']
