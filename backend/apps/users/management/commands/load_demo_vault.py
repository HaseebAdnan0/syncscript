"""
Management command to test loading demo vault fixture data.
This command validates the fixture structure and demonstrates how to load it.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test loading demo vault fixture data'

    def handle(self, *args, **options):
        fixture_path = Path(__file__).parent.parent.parent / 'fixtures' / 'demo_vault.json'

        if not fixture_path.exists():
            self.stdout.write(self.style.ERROR(f'Fixture file not found: {fixture_path}'))
            return

        try:
            with open(fixture_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            required_keys = ['vault', 'sources', 'annotations']
            for key in required_keys:
                if key not in data:
                    self.stdout.write(self.style.ERROR(f'Missing required key: {key}'))
                    return

            # Validate vault data
            vault_data = data['vault']
            if not vault_data.get('name') or not vault_data.get('description'):
                self.stdout.write(self.style.ERROR('Vault must have name and description'))
                return

            # Validate sources
            sources = data['sources']
            if len(sources) < 10:
                self.stdout.write(self.style.WARNING(f'Expected at least 10 sources, got {len(sources)}'))

            for idx, source in enumerate(sources):
                required_source_fields = ['url', 'title', 'source_type']
                for field in required_source_fields:
                    if field not in source:
                        self.stdout.write(self.style.ERROR(f'Source {idx} missing field: {field}'))
                        return

            # Validate annotations
            annotations = data['annotations']
            if len(annotations) < 15:
                self.stdout.write(self.style.WARNING(f'Expected at least 15 annotations, got {len(annotations)}'))

            for idx, annotation in enumerate(annotations):
                required_annotation_fields = ['source_index', 'content']
                for field in required_annotation_fields:
                    if field not in annotation:
                        self.stdout.write(self.style.ERROR(f'Annotation {idx} missing field: {field}'))
                        return

                # Validate source_index is valid
                if annotation['source_index'] >= len(sources):
                    self.stdout.write(self.style.ERROR(f'Annotation {idx} has invalid source_index: {annotation["source_index"]}'))
                    return

                # Validate parent_index if present
                if annotation.get('parent_index') is not None:
                    parent_idx = annotation['parent_index']
                    if parent_idx >= idx:
                        self.stdout.write(self.style.ERROR(f'Annotation {idx} has invalid parent_index: {parent_idx} (must be < {idx})'))
                        return

            # Count threading examples
            threaded_count = sum(1 for a in annotations if a.get('parent_index') is not None)

            self.stdout.write(self.style.SUCCESS('✓ Fixture validation passed!'))
            self.stdout.write(f'  Vault: {vault_data["name"]}')
            self.stdout.write(f'  Sources: {len(sources)}')
            self.stdout.write(f'  Annotations: {len(annotations)} ({threaded_count} threaded)')

            # Show sample data
            self.stdout.write('\nSample sources:')
            for source in sources[:3]:
                self.stdout.write(f'  - {source["title"]}')

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
