import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User, EmailPreference
from django.db import transaction

try:
    with transaction.atomic():
        test_user = User.objects.create_user(
            username='signal_test_xyz',
            email='signal_test_xyz@test.com',
            password='testpass123'
        )
        print(f'✓ User created: {test_user.email}')

        try:
            pref = test_user.email_preference
            print(f'✓ EmailPreference auto-created via signal')
            print(f'  - collaboration_notifications: {pref.collaboration_notifications}')
            print(f'  - marketing_emails: {pref.marketing_emails}')
            print(f'  - unsubscribe_token length: {len(pref.unsubscribe_token)}')
            print(f'✓ Signal working correctly!')
        except EmailPreference.DoesNotExist:
            print('✗ EmailPreference was NOT created - signal not working')
            raise

        # Force rollback
        raise Exception('Rollback test transaction')
except Exception as e:
    if 'Rollback' in str(e):
        print('\n✓ Test transaction rolled back (no data saved)')
        print('✓ US-010 acceptance criteria verified!')
    else:
        raise
