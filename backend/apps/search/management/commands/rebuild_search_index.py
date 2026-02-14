"""
Management command to rebuild search vectors for existing Sources and Annotations.

Usage:
    python manage.py rebuild_search_index
    python manage.py rebuild_search_index --sources-only
    python manage.py rebuild_search_index --annotations-only
"""
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from django.db.models import F

from apps.sources.models import Source
from apps.annotations.models import Annotation


class Command(BaseCommand):
    help = 'Rebuild search vectors for Sources and Annotations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sources-only',
            action='store_true',
            help='Only rebuild search vectors for Sources',
        )
        parser.add_argument(
            '--annotations-only',
            action='store_true',
            help='Only rebuild search vectors for Annotations',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process per batch (default: 100)',
        )

    def handle(self, *args, **options):
        sources_only = options['sources_only']
        annotations_only = options['annotations_only']
        batch_size = options['batch_size']

        # If neither flag is set, rebuild both
        rebuild_sources = not annotations_only
        rebuild_annotations = not sources_only

        if rebuild_sources:
            self.rebuild_source_vectors(batch_size)

        if rebuild_annotations:
            self.rebuild_annotation_vectors(batch_size)

        self.stdout.write(self.style.SUCCESS('\nSearch index rebuild complete!'))

    def rebuild_source_vectors(self, batch_size):
        """Rebuild search vectors for all Sources"""
        self.stdout.write('\nRebuilding Source search vectors...')

        # Get total count
        total = Source.objects.filter(is_deleted=False).count()
        self.stdout.write(f'Found {total} sources to process')

        if total == 0:
            self.stdout.write(self.style.WARNING('No sources to process'))
            return

        # Process in batches
        processed = 0
        batch_num = 0

        while processed < total:
            batch_num += 1
            offset = processed
            limit = min(batch_size, total - processed)

            self.stdout.write(f'Processing batch {batch_num} ({offset}-{offset + limit})...')

            # Get batch of sources
            sources = Source.objects.filter(is_deleted=False)[offset:offset + limit]

            # Update search vectors in bulk
            for source in sources:
                # Build search vector with weights
                search_vector = (
                    SearchVector('title', weight='A', config='english') +
                    SearchVector('description', weight='B', config='english')
                )

                # Update the source
                Source.objects.filter(pk=source.pk).update(
                    search_vector=search_vector
                )

            processed += len(sources)
            self.stdout.write(self.style.SUCCESS(f'  Processed {processed}/{total} sources'))

        self.stdout.write(self.style.SUCCESS(f'Completed {total} sources'))

    def rebuild_annotation_vectors(self, batch_size):
        """Rebuild search vectors for all Annotations"""
        self.stdout.write('\nRebuilding Annotation search vectors...')

        # Get total count
        total = Annotation.objects.filter(source__is_deleted=False).count()
        self.stdout.write(f'Found {total} annotations to process')

        if total == 0:
            self.stdout.write(self.style.WARNING('No annotations to process'))
            return

        # Process in batches
        processed = 0
        batch_num = 0

        while processed < total:
            batch_num += 1
            offset = processed
            limit = min(batch_size, total - processed)

            self.stdout.write(f'Processing batch {batch_num} ({offset}-{offset + limit})...')

            # Get batch of annotations
            annotations = Annotation.objects.filter(source__is_deleted=False)[offset:offset + limit]

            # Update search vectors in bulk
            for annotation in annotations:
                # Build search vector (content only, weight A)
                search_vector = SearchVector('content', weight='A', config='english')

                # Update the annotation
                Annotation.objects.filter(pk=annotation.pk).update(
                    search_vector=search_vector
                )

            processed += len(annotations)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Processed {processed}/{total} annotations'))

        self.stdout.write(self.style.SUCCESS(f'Completed {total} annotations'))
