"""
Signal handlers for AI app to maintain cache freshness.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.sources.models import Source


@receiver(post_save, sender=Source)
def invalidate_vault_insights_on_source_save(sender, instance, **kwargs):
    """
    Invalidate vault AI insights cache when a source is created or updated.
    This ensures insights stay fresh when vault contents change.
    """
    vault = instance.vault
    if vault.ai_insights_cache is not None:
        vault.ai_insights_updated_at = None
        vault.save(update_fields=['ai_insights_updated_at'])


@receiver(post_delete, sender=Source)
def invalidate_vault_insights_on_source_delete(sender, instance, **kwargs):
    """
    Invalidate vault AI insights cache when a source is deleted.
    This ensures insights stay fresh when vault contents change.
    """
    vault = instance.vault
    if vault.ai_insights_cache is not None:
        vault.ai_insights_updated_at = None
        vault.save(update_fields=['ai_insights_updated_at'])
