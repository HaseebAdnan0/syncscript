"""Tests for immediate email notification task"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from unittest.mock import patch

from apps.notifications.models import Notification, NotificationPreferences
from apps.notifications.tasks import send_immediate_notification_email


User = get_user_model()


class ImmediateEmailTaskTestCase(TestCase):
    """Test send_immediate_notification_email Celery task"""

    def setUp(self) -> None:
        """Create test user and notification"""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create notification
        self.notification = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Test Notification',
            body='Test body',
            data={}
        )

    def test_sends_email_when_preference_is_immediate(self) -> None:
        """Email should be sent when user has immediate preference"""
        # Set preference to immediate
        prefs = self.user.notification_preferences  # type: ignore[attr-defined]
        prefs.email_digest_frequency = 'immediate'
        prefs.save()

        # Run task
        result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify email sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('Test Notification', mail.outbox[0].subject)

        # Verify notification marked as emailed
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.emailed_at)

    def test_does_not_send_email_when_preference_is_daily(self) -> None:
        """Email should not be sent when user has daily preference"""
        # Set preference to daily
        prefs = self.user.notification_preferences  # type: ignore[attr-defined]
        prefs.email_digest_frequency = 'daily'
        prefs.save()

        # Run task
        result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify no email sent
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

        # Verify notification NOT marked as emailed
        self.notification.refresh_from_db()
        self.assertIsNone(self.notification.emailed_at)

    def test_does_not_send_email_when_preference_is_weekly(self) -> None:
        """Email should not be sent when user has weekly preference"""
        # Set preference to weekly
        prefs = self.user.notification_preferences  # type: ignore[attr-defined]
        prefs.email_digest_frequency = 'weekly'
        prefs.save()

        # Run task
        result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify no email sent
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_does_not_send_email_when_preference_is_none(self) -> None:
        """Email should not be sent when user has none preference"""
        # Set preference to none
        prefs = self.user.notification_preferences  # type: ignore[attr-defined]
        prefs.email_digest_frequency = 'none'
        prefs.save()

        # Run task
        result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify no email sent
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_handles_missing_notification(self) -> None:
        """Task should handle non-existent notification gracefully"""
        # Run task with invalid ID
        result = send_immediate_notification_email(99999)  # type: ignore[attr-defined]

        # Verify task returns False
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_handles_missing_preferences(self) -> None:
        """Task should handle user without preferences gracefully"""
        # Delete preferences
        self.user.notification_preferences.delete()  # type: ignore[attr-defined]

        # Run task
        result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify no email sent
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_marks_notification_as_emailed_only_on_success(self) -> None:
        """Notification should only be marked as emailed if email succeeds"""
        # Set preference to immediate
        prefs = self.user.notification_preferences  # type: ignore[attr-defined]
        prefs.email_digest_frequency = 'immediate'
        prefs.save()

        # Mock send_notification_email to fail
        with patch('apps.notifications.tasks.send_notification_email', return_value=False):
            result = send_immediate_notification_email(self.notification.id)  # type: ignore[attr-defined]

        # Verify task returns False
        self.assertFalse(result)

        # Verify notification NOT marked as emailed
        self.notification.refresh_from_db()
        self.assertIsNone(self.notification.emailed_at)
