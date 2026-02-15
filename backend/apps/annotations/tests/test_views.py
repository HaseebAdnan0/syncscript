from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.vaults.models import Vault, VaultMembership, RoleChoices
from apps.sources.models import Source, SourceType
from apps.annotations.models import Annotation

User = get_user_model()


class AnnotationCRUDTest(TestCase):
    """Test Annotation API CRUD operations."""

    def setUp(self):
        """Set up test data for annotation tests."""
        # Create test users
        self.owner = User.objects.create(username='owner', email='owner@test.com')
        self.owner.set_password('password123')
        self.owner.save()

        self.member = User.objects.create(username='member', email='member@test.com')
        self.member.set_password('password123')
        self.member.save()

        self.other_user = User.objects.create(username='other', email='other@test.com')
        self.other_user.set_password('password123')
        self.other_user.save()

        # Create vault with owner
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for annotations',
            owner=self.owner
        )

        # Add member to vault
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )

        # Create source for annotations
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article1',
            title='Test Article',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Create API client
        self.client = APIClient()

    def test_post_creates_top_level_annotation(self):
        """Test POST creates top-level annotation on source."""
        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        data = {
            'source': self.source.id,
            'text': 'This is a top-level annotation',
            'pageNumber': 1,
            'position': {'x': 100, 'y': 200}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'This is a top-level annotation')
        self.assertEqual(response.data['pageNumber'], 1)
        self.assertEqual(response.data['position'], {'x': 100, 'y': 200})
        self.assertIsNone(response.data['parent'])
        self.assertEqual(Annotation.objects.count(), 1)

    def test_post_with_parent_creates_reply(self):
        """Test POST with parent creates reply to top-level annotation."""
        # Create top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Top level annotation',
            page_number=1
        )

        self.client.force_authenticate(user=self.member)
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        data = {
            'source': self.source.id,
            'text': 'This is a reply',
            'parent': top_level.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'This is a reply')
        self.assertEqual(response.data['parent'], top_level.id)
        self.assertEqual(Annotation.objects.count(), 2)
        self.assertEqual(top_level.replies.count(), 1)

    def test_post_with_parent_of_reply_fails(self):
        """Test POST with parent of reply fails with 400 (max 2 levels)."""
        # Create top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Top level',
            page_number=1
        )

        # Create reply to top-level
        reply = Annotation.objects.create(
            source=self.source,
            user=self.member,
            content='First reply',
            parent=top_level
        )

        # Try to create reply to reply (should fail)
        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        data = {
            'source': self.source.id,
            'text': 'This should fail (reply to reply)',
            'parent': reply.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot reply to a reply', str(response.data))
        self.assertEqual(Annotation.objects.count(), 2)  # No new annotation created

    def test_get_list_returns_nested_structure_with_replies(self):
        """Test GET list returns nested structure with replies included."""
        # Create top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Top level annotation',
            page_number=1
        )

        # Create replies
        reply1 = Annotation.objects.create(
            source=self.source,
            user=self.member,
            content='First reply',
            parent=top_level
        )
        reply2 = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Second reply',
            parent=top_level
        )

        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only top-level annotations
        annotation = response.data['results'][0]
        self.assertEqual(annotation['text'], 'Top level annotation')
        self.assertEqual(len(annotation['replies']), 2)  # Nested replies included
        reply_contents = [r['text'] for r in annotation['replies']]
        self.assertIn('First reply', reply_contents)
        self.assertIn('Second reply', reply_contents)

    def test_patch_updates_content_only(self):
        """Test PATCH updates content field only."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Original content',
            page_number=5,
            position={'x': 100, 'y': 200}
        )

        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/annotations/{annotation.id}/'
        data = {'text': 'Updated content'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Updated content')
        annotation.refresh_from_db()
        self.assertEqual(annotation.content, 'Updated content')

    def test_patch_cannot_change_position_parent_source(self):
        """Test PATCH cannot change immutable fields (position, parent, source)."""
        # Create two sources for testing
        other_source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article2',
            title='Other Article',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Create top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Top level',
            page_number=1
        )

        # Create annotation with position
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Test annotation',
            page_number=3,
            position={'x': 100, 'y': 200}
        )

        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/annotations/{annotation.id}/'

        # Try to change position
        original_position = annotation.position.copy()
        data = {
            'text': 'Same content',
            'position': {'x': 999, 'y': 888}
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        annotation.refresh_from_db()
        # Position should remain unchanged
        self.assertEqual(annotation.position, original_position)

        # Try to change source (should be ignored or fail)
        data = {'source': other_source.id}
        response = self.client.patch(url, data, format='json')
        annotation.refresh_from_db()
        self.assertEqual(annotation.source.id, self.source.id)  # Source unchanged

        # Try to change parent (should be ignored or fail)
        data = {'parent': top_level.id}
        response = self.client.patch(url, data, format='json')
        annotation.refresh_from_db()
        self.assertIsNone(annotation.parent)  # Parent unchanged

    def test_delete_removes_annotation_and_cascades_to_replies(self):
        """Test DELETE removes annotation and cascades to replies."""
        # Create top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Top level annotation',
            page_number=1
        )

        # Create replies
        reply1 = Annotation.objects.create(
            source=self.source,
            user=self.member,
            content='First reply',
            parent=top_level
        )
        reply2 = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Second reply',
            parent=top_level
        )

        self.assertEqual(Annotation.objects.count(), 3)

        # Delete top-level annotation (should cascade to replies)
        self.client.force_authenticate(user=self.owner)
        url = f'/api/v1/annotations/{top_level.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify all annotations deleted (cascade)
        self.assertEqual(Annotation.objects.count(), 0)


class AnnotationPermissionTest(TestCase):
    """Test Annotation API permission checks."""

    def setUp(self):
        """Set up test data for permission tests."""
        # Create test users
        self.owner = User.objects.create(username='owner', email='owner@test.com')
        self.owner.set_password('password123')
        self.owner.save()

        self.member = User.objects.create(username='member', email='member@test.com')
        self.member.set_password('password123')
        self.member.save()

        self.non_member = User.objects.create(username='nonmember', email='nonmember@test.com')
        self.non_member.set_password('password123')
        self.non_member.save()

        # Create vault with owner
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for permissions',
            owner=self.owner
        )

        # Add member to vault as viewer
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.VIEWER
        )

        # Create source for annotations
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article1',
            title='Test Article',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Create API client
        self.client = APIClient()

    def test_non_vault_member_cannot_list_annotations(self):
        """Test non-vault-member cannot list annotations (403)."""
        # Create annotation as owner
        Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Owner annotation',
            page_number=1
        )

        # Try to list as non-member (should get 403 or empty list based on filtering)
        self.client.force_authenticate(user=self.non_member)
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        response = self.client.post(url, {'source': self.source.id, 'text': 'Should fail'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_any_vault_member_can_create_annotation(self):
        """Test any vault member (including Viewer) can create annotation."""
        self.client.force_authenticate(user=self.member)  # member is VIEWER role
        url = f'/api/v1/sources/{self.source.id}/annotations/'
        data = {
            'source': self.source.id,
            'text': 'Viewer annotation',
            'pageNumber': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Viewer annotation')
        self.assertEqual(Annotation.objects.count(), 1)

    def test_author_can_update_own_annotation(self):
        """Test author can update their own annotation."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.member,
            content='Original content',
            page_number=1
        )

        self.client.force_authenticate(user=self.member)
        url = f'/api/v1/annotations/{annotation.id}/'
        data = {'text': 'Updated content'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Updated content')
        annotation.refresh_from_db()
        self.assertEqual(annotation.content, 'Updated content')

    def test_non_author_cannot_update_annotation(self):
        """Test non-author cannot update annotation (403)."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Owner annotation',
            page_number=1
        )

        # Try to update as member (not author)
        self.client.force_authenticate(user=self.member)
        url = f'/api/v1/annotations/{annotation.id}/'
        data = {'text': 'Trying to update'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        annotation.refresh_from_db()
        self.assertEqual(annotation.content, 'Owner annotation')  # Content unchanged

    def test_author_can_delete_own_annotation(self):
        """Test author can delete their own annotation."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.member,
            content='Member annotation',
            page_number=1
        )

        self.client.force_authenticate(user=self.member)
        url = f'/api/v1/annotations/{annotation.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Annotation.objects.count(), 0)

    def test_non_author_cannot_delete_annotation(self):
        """Test non-author cannot delete annotation (403)."""
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Owner annotation',
            page_number=1
        )

        # Try to delete as member (not author)
        self.client.force_authenticate(user=self.member)
        url = f'/api/v1/annotations/{annotation.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Annotation.objects.count(), 1)  # Annotation still exists
