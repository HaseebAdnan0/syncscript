"""
Onboarding service for creating demo vaults for new users.
"""
import json
from pathlib import Path
from django.db import transaction
from apps.vaults.models import Vault
from apps.sources.models import Source
from apps.annotations.models import Annotation


def create_demo_vault(user):
    """
    Creates a demo vault for a user populated with demo content.

    Args:
        user: User instance who will own the vault

    Returns:
        Vault instance

    Raises:
        FileNotFoundError: If demo_vault.json fixture not found
        json.JSONDecodeError: If fixture is malformed
    """
    # Check if demo vault already exists for this user
    existing_vault = Vault.objects.filter(
        owner=user,
        name="AI Research Papers 2025"
    ).first()

    if existing_vault:
        return existing_vault

    # Load demo vault fixture
    fixture_path = Path(__file__).parent.parent / 'fixtures' / 'demo_vault.json'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        demo_data = json.load(f)

    # Create vault and related objects in a transaction
    with transaction.atomic():
        # Create vault (signal will auto-create owner membership)
        vault = Vault.objects.create(
            name=demo_data['vault']['name'],
            description=demo_data['vault']['description'],
            owner=user
        )

        # Create sources
        sources = []
        for source_data in demo_data['sources']:
            source = Source.objects.create(
                vault=vault,
                url=source_data['url'],
                title=source_data['title'],
                description=source_data['description'],
                source_type=source_data['source_type'],
                metadata=source_data['metadata'],
                created_by=user
            )
            sources.append(source)

        # Create annotations (using source_index and parent_index from fixture)
        annotations = []
        for annotation_data in demo_data['annotations']:
            source_index = annotation_data['source_index']
            parent_index = annotation_data.get('parent_index')

            # Resolve parent if it exists
            parent = None
            if parent_index is not None:
                parent = annotations[parent_index]

            annotation = Annotation.objects.create(
                source=sources[source_index],
                user=user,
                content=annotation_data['content'],
                page_number=annotation_data.get('page_number'),
                position=annotation_data.get('position', {}),
                parent=parent
            )
            annotations.append(annotation)

    return vault
