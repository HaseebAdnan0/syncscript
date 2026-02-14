"""
Django signals for automatic search vector updates.

Post-save signals trigger Celery tasks to update search vectors
when Source or Annotation models are modified.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='sources.Source')
def update_source_search_vector_on_save(sender, instance, created, update_fields, **kwargs):
    """
    Trigger search vector update when a Source is created or modified.

    Only triggers when relevant fields (title, description) change.
    """
    from apps.search.tasks import update_source_search_vector

    # If update_fields is specified, check if relevant fields were updated
    if update_fields is not None:
        relevant_fields = {'title', 'description', 'metadata'}
        if not relevant_fields.intersection(update_fields):
            return  # No relevant fields changed, skip update

    # Queue Celery task to update search vector
    update_source_search_vector.delay(instance.id)


@receiver(post_save, sender='annotations.Annotation')
def update_annotation_search_vector_on_save(sender, instance, created, update_fields, **kwargs):
    """
    Trigger search vector update when an Annotation is created or modified.

    Only triggers when the content field changes.
    """
    from apps.search.tasks import update_annotation_search_vector

    # If update_fields is specified, check if content was updated
    if update_fields is not None:
        if 'content' not in update_fields:
            return  # Content field not changed, skip update

    # Queue Celery task to update search vector
    update_annotation_search_vector.delay(instance.id)
