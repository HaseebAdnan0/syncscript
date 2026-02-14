#!/usr/bin/env python
"""Simple test for citation export endpoint"""
import os
import sys
import django

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.users.models import User
from apps.vaults.models import Vault
from apps.sources.models import Source
from rest_framework.test import APIClient

# Clean up
User.objects.filter(email='testexport@example.com').delete()

# Create test data
user = User.objects.create_user(
    email='testexport@example.com',
    username='testexportuser',
    password='testpass123'
)

vault = Vault.objects.create(
    name='Export Test Vault',
    description='Test',
    owner=user
)

source = Source.objects.create(
    vault=vault,
    title='Test Source',
    url='https://example.com',
    created_by=user,
    source_type='WEBSITE',
    metadata={
        'authors': ['Test Author'],
        'publication_date': '2024'
    }
)

print(f'Created vault: {vault.id}, owner: {vault.owner.email}')
print(f'Created source: {source.id}')

# Test with API client
client = APIClient()
client.force_authenticate(user=user)

url = f'/api/v1/vaults/{vault.id}/citations/export/'
print(f'\nTesting URL: {url}')

response = client.get(url, {'format': 'bibtex'})
print(f'Status: {response.status_code}')

if response.status_code == 200:
    print('SUCCESS!')
    print(f'Content-Type: {response["Content-Type"]}')
    print(f'Content-Disposition: {response.get("Content-Disposition", "N/A")}')
    print(f'Content length: {len(response.content)} bytes')
else:
    if hasattr(response, 'data'):
        print(f'Response data: {response.data}')
    else:
        print(f'Response content: {response.content.decode()[:500]}')

# Cleanup
vault.delete()
user.delete()
print('\nCleaned up')
