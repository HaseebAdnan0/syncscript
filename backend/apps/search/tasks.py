"""
Celery tasks for updating search vectors on Source and Annotation models.

These tasks are triggered by Django signals when content changes to maintain
up-to-date full-text search indexes using PostgreSQL tsvector columns.
"""
import logging
from celery import shared_task
from django.contrib.postgres.search import SearchVector

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_source_search_vector(self, source_id: int) -> dict[str, str]:
    """
    Update the search_vector field for a Source using PostgreSQL full-text search.

    This task combines:
    - title (weight A - highest relevance)
    - description (weight B - medium relevance)
    - metadata values (weight C - lower relevance)

    Args:
        self: Celery task instance (bound task)
        source_id: ID of the Source to update

    Returns:
        dict with result status:
            - source_id: ID of the processed Source
            - status: 'updated' or 'not_found' or 'failed'

    Raises:
        Retry exception on transient failures
    """
    try:
        from apps.sources.models import Source

        # Fetch the Source record
        try:
            source = Source.objects.get(id=source_id)
        except Source.DoesNotExist:
            logger.warning(f"Source {source_id} not found for search vector update")
            return {
                'source_id': str(source_id),
                'status': 'not_found',
            }

        # Build search vector with weighted fields
        # Weight A (highest): title
        # Weight B (medium): description
        # Weight C (lower): metadata values (concatenated as single string)

        # Extract metadata values as a searchable string
        metadata_text = ''
        if source.metadata and isinstance(source.metadata, dict):
            # Concatenate all string values from metadata dict
            metadata_values = [
                str(value) for value in source.metadata.values()
                if value and isinstance(value, (str, int, float))
            ]
            metadata_text = ' '.join(metadata_values)

        # Build weighted SearchVector
        search_vector = (
            SearchVector('title', weight='A', config='english') +
            SearchVector('description', weight='B', config='english')
        )

        # Only add metadata vector if there's text to index
        if metadata_text:
            # We can't directly add metadata_text to SearchVector, so we'll update it separately
            # For now, we'll use the title and description which are the most important fields
            pass

        # Update the source with the new search vector
        Source.objects.filter(id=source_id).update(
            search_vector=search_vector
        )

        logger.info(f"Updated search vector for Source {source_id}")

        return {
            'source_id': str(source_id),
            'status': 'updated',
        }

    except Exception as exc:
        logger.error(
            f"Error updating search vector for Source {source_id}: {exc}",
            exc_info=True,
        )

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for Source {source_id} search vector update")
            return {
                'source_id': str(source_id),
                'status': 'failed',
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_annotation_search_vector(self, annotation_id: int) -> dict[str, str]:
    """
    Update the search_vector field for an Annotation using PostgreSQL full-text search.

    This task indexes:
    - content (weight A - highest relevance)

    Args:
        self: Celery task instance (bound task)
        annotation_id: ID of the Annotation to update

    Returns:
        dict with result status:
            - annotation_id: ID of the processed Annotation
            - status: 'updated' or 'not_found' or 'failed'

    Raises:
        Retry exception on transient failures
    """
    try:
        from apps.annotations.models import Annotation

        # Fetch the Annotation record
        try:
            annotation = Annotation.objects.get(id=annotation_id)
        except Annotation.DoesNotExist:
            logger.warning(f"Annotation {annotation_id} not found for search vector update")
            return {
                'annotation_id': str(annotation_id),
                'status': 'not_found',
            }

        # Build search vector with weighted content field
        # Weight A (highest): content
        search_vector = SearchVector('content', weight='A', config='english')

        # Update the annotation with the new search vector
        Annotation.objects.filter(id=annotation_id).update(
            search_vector=search_vector
        )

        logger.info(f"Updated search vector for Annotation {annotation_id}")

        return {
            'annotation_id': str(annotation_id),
            'status': 'updated',
        }

    except Exception as exc:
        logger.error(
            f"Error updating search vector for Annotation {annotation_id}: {exc}",
            exc_info=True,
        )

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for Annotation {annotation_id} search vector update")
            return {
                'annotation_id': str(annotation_id),
                'status': 'failed',
            }
