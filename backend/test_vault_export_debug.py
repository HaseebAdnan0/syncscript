#!/usr/bin/env python
"""Quick debug script to test vault export endpoint"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.vaults.models import Vault
from apps.sources.models import Source

# Create test database entities
user = User.objects.create_user('testcite@example.com', 'testcite', 'testpass123')
vault = Vault.objects.create(name='Test Export Vault', owner=user)
print(f'Created vault {vault.id} with owner {user.email}')

# Create a source
source = Source.objects.create(
    vault=vault,
    title='Test Article',
    url='https://example.com/test',
    created_by=user,
    metadata={
        'authors': ['Test Author'],
        'publication_date': '2024-01-01',
        'journal': 'Test Journal'
    }
)
print(f'Created source: {source.title}')

# Check queryset
from django.db.models import Q
vaults = Vault.objects.filter(Q(owner=user) | Q(members=user)).distinct()
print(f'Vaults in queryset: {vaults.count()}')
print(f'Vault IDs: {[str(v.id) for v in vaults]}')

# Test with APIClient
client = APIClient()
client.force_authenticate(user=user)

# Try to access the vault
response = client.get(f'/api/v1/vaults/{vault.id}/')
print(f'GET /api/v1/vaults/{vault.id}/ => {response.status_code}')

# Try export endpoint
response = client.get(f'/api/v1/vaults/{vault.id}/citations/export/', {'format': 'apa7'})
print(f'GET /api/v1/vaults/{vault.id}/citations/export/?format=apa7 => {response.status_code}')
if response.status_code != 200:
    print(f'Response: {response.data if hasattr(response, "data") else response.content}')
else:
    print(f'Success! Content-Type: {response["Content-Type"]}')
    print(f'Content length: {len(response.content)} bytes')

# Cleanup
source.delete()
vault.delete()
user.delete()
print('Cleaned up test data')
