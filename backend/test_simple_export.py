"""
Simple standalone test for export endpoint
"""
from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.vaults.models import Vault
from apps.sources.models import Source


class SimpleExportTest(TestCase):
    def test_export_works(self):
        # Create user
        user = User.objects.create_user('simple@test.com', 'simpleuser', 'pass123')

        # Create vault
        vault = Vault.objects.create(name='Simple Vault', owner=user)

        # Create source
        source = Source.objects.create(
            vault=vault,
            title='Test Article',
            url='https://example.com/test',
            created_by=user,
            metadata={
                'authors': ['Author Name'],
                'publication_date': '2024-01-01',
                'journal': 'Test Journal'
            }
        )

        # Create client and authenticate
        client = APIClient()
        client.force_authenticate(user=user)

        # Test export
        url = f'/api/v1/vaults/{vault.id}/citations/export/'
        print(f'\nTesting: {url}')

        response = client.get(url, {'format': 'bibtex'})
        print(f'Response: {response.status_code}')
        if response.status_code != 200:
            print(f'Error: {response.data if hasattr(response, "data") else response.content}')

        self.assertEqual(response.status_code, 200)
