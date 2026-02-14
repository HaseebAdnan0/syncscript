"""
Django signals for citation cache invalidation.
"""
from typing import Any
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender='sources.Source')
def invalidate_cache_on_metadata_change(sender: Any, instance: Any, **kwargs: Any) -> None:
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
            old_metadata = dirty_fields.get('metadata', {})
            new_metadata = instance.metadata or {}

            # Only invalidate if metadata changed in a way that affects citations
            # (not just adding citations to the cache)
            if old_metadata != new_metadata:
                # Check if the only change is adding/updating citations
                old_without_citations = {k: v for k, v in old_metadata.items() if k != 'citations'}
                new_without_citations = {k: v for k, v in new_metadata.items() if k != 'citations'}

                # If non-citation metadata changed, invalidate cache
                if old_without_citations != new_without_citations:
                    if 'citations' in new_metadata:
                        del instance.metadata['citations']
