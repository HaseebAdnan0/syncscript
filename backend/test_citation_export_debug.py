#!/usr/bin/env python
"""Debug script for citation export endpoint"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.vaults.models import Vault
from apps.sources.models import Source
from rest_framework.test import APIClient

# Clean up
User.objects.filter(email='debug@test.com').delete()

# Create test data
user = User.objects.create_user(
    email='debug@test.com',
    username='debuguser',
    password='testpass123'
)

vault = Vault.objects.create(
    name='Debug Vault',
    description='Debug vault',
    owner=user
)

source = Source.objects.create(
    vault=vault,
    title='Debug Source',
    url='https://example.com',
    created_by=user,
    source_type='WEBSITE',
    metadata={
        'authors': ['Test Author'],
        'publication_date': '2024'
    }
)

print(f'Created vault with ID: {vault.id}')
print(f'Created source with ID: {source.id}')

# Test the endpoint
client = APIClient()
client.force_authenticate(user=user)

url = f'/api/v1/vaults/{vault.id}/citations/'
print(f'\nTesting URL: {url}')

response = client.get(url, {'format': 'bibtex'})
print(f'Response status: {response.status_code}')

if hasattr(response, 'data'):
    print(f'Response data: {response.data}')
else:
    print(f'Response content (first 500 chars): {response.content.decode()[:500]}')

# Cleanup
vault.delete()
user.delete()
print('\nCleaned up test data')
