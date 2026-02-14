from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.vaults.models import Vault
from apps.sources.models import Source
from apps.annotations.models import Annotation

User = get_user_model()


class AnnotationModelTest(TestCase):
    """Test suite for Annotation model constraints and threading behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()

        self.vault = Vault.objects.create(
            name='Test Vault',
            description='A test vault',
            owner=self.user
        )

        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            created_by=self.user
        )

    def test_create_top_level_annotation_succeeds(self):
        """Test creating top-level annotation (parent=None) succeeds."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='This is a top-level annotation',
            page_number=1,
            position={'x': 100, 'y': 200},
            parent=None
        )

        self.assertEqual(annotation.source, self.source)
        self.assertEqual(annotation.user, self.user)
        self.assertEqual(annotation.content, 'This is a top-level annotation')
        self.assertEqual(annotation.page_number, 1)
        self.assertEqual(annotation.position, {'x': 100, 'y': 200})
        self.assertIsNone(annotation.parent)
        self.assertIsNotNone(annotation.created_at)
        self.assertIsNotNone(annotation.updated_at)

    def test_create_reply_to_top_level_succeeds(self):
        """Test creating reply to top-level (parent=top_level) succeeds."""
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Top-level annotation',
            parent=None
        )

        reply = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Reply to top-level annotation',
            parent=top_level
        )

        self.assertEqual(reply.parent, top_level)
        self.assertEqual(reply.source, self.source)
        self.assertEqual(reply.user, self.user)
        self.assertEqual(reply.content, 'Reply to top-level annotation')
        self.assertIsNotNone(reply.created_at)

        # Verify the reverse relation works
        self.assertEqual(top_level.replies.count(), 1)
        self.assertEqual(top_level.replies.first(), reply)

    def test_create_reply_to_reply_raises_validation_error(self):
        """Test creating reply to reply raises ValidationError."""
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Top-level annotation',
            parent=None
        )

        reply = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='First-level reply',
            parent=top_level
        )

        # Attempting to create a reply to a reply should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            Annotation.objects.create(
                source=self.source,
                user=self.user,
                content='Reply to reply (should fail)',
                parent=reply
            )

        self.assertIn('Maximum nesting level (2) exceeded', str(context.exception))

    def test_position_json_field_stores_complex_objects(self):
        """Test position JSON field stores complex objects."""
        complex_position = {
            'type': 'highlight',
            'coordinates': {
                'x1': 100,
                'y1': 200,
                'x2': 300,
                'y2': 250
            },
            'page': 5,
            'color': '#FFFF00',
            'metadata': {
                'selected_text': 'This is the highlighted text',
                'timestamp': '2024-01-15T10:30:00Z'
            }
        }

        annotation = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Complex position annotation',
            position=complex_position
        )

        # Retrieve from database to ensure proper serialization
        saved_annotation = Annotation.objects.get(id=annotation.id)
        self.assertEqual(saved_annotation.position, complex_position)
        self.assertEqual(saved_annotation.position['type'], 'highlight')
        self.assertEqual(saved_annotation.position['coordinates']['x1'], 100)
        self.assertEqual(saved_annotation.position['metadata']['selected_text'], 'This is the highlighted text')

    def test_cascade_delete_removes_annotations_when_source_deleted(self):
        """Test cascade delete removes annotations when source deleted."""
        # Create top-level annotation and replies
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Top-level annotation',
            parent=None
        )

        reply1 = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Reply 1',
            parent=top_level
        )

        reply2 = Annotation.objects.create(
            source=self.source,
            user=self.user,
            content='Reply 2',
            parent=top_level
        )

        # Verify annotations exist
        self.assertEqual(Annotation.objects.filter(source=self.source).count(), 3)

        # Delete source
        self.source.delete()

        # Verify all annotations were cascade deleted
        self.assertEqual(Annotation.objects.filter(id=top_level.id).count(), 0)
        self.assertEqual(Annotation.objects.filter(id=reply1.id).count(), 0)
        self.assertEqual(Annotation.objects.filter(id=reply2.id).count(), 0)
        self.assertEqual(Annotation.objects.count(), 0)
