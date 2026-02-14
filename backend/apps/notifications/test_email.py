"""Tests for email notification service."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from apps.notifications.models import Notification
from apps.notifications.email import send_notification_email

User = get_user_model()


class EmailNotificationServiceTestCase(TestCase):
    """Test suite for send_notification_email function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_send_single_notification_email(self) -> None:
        """Test sending email with single notification."""
        notification = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='You were invited to a vault',
            body='John invited you to Research Vault',
            data={'vault_id': 123}
        )

        result = send_notification_email(self.user, [notification])

        # Assert email was sent successfully
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        # Check email content
        email = mail.outbox[0]
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('You were invited to a vault', email.subject)
        self.assertIn('testuser', email.body)
        self.assertIn('You were invited to a vault', email.body)

        # Check HTML alternative exists
        self.assertEqual(len(email.alternatives), 1)  # type: ignore[attr-defined]
        html_content, content_type = email.alternatives[0]  # type: ignore[attr-defined]
        self.assertEqual(content_type, 'text/html')

    def test_send_multiple_notifications_email(self) -> None:
        """Test sending email with multiple notifications."""
        notifications = [
            Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title='Notification 1',
                body='Body 1',
                data={}
            ),
            Notification.objects.create(
                user=self.user,
                type='source_added',
                title='Notification 2',
                body='Body 2',
                data={}
            ),
            Notification.objects.create(
                user=self.user,
                type='mention',
                title='Notification 3',
                body='Body 3',
                data={}
            ),
        ]

        result = send_notification_email(self.user, notifications)

        # Assert email was sent successfully
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        # Check email content
        email = mail.outbox[0]
        self.assertIn('3 new notifications', email.subject)
        self.assertIn('Notification 1', email.body)
        self.assertIn('Notification 2', email.body)
        self.assertIn('Notification 3', email.body)

    def test_empty_notification_list_returns_false(self) -> None:
        """Test that empty notification list returns False without sending."""
        result = send_notification_email(self.user, [])

        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_includes_plain_text_and_html(self) -> None:
        """Test email includes both plain text and HTML versions."""
        notification = Notification.objects.create(
            user=self.user,
            type='mention',
            title='Test Notification',
            body='Test body content',
            data={}
        )

        send_notification_email(self.user, [notification])

        email = mail.outbox[0]

        # Check plain text body
        self.assertIn('Test Notification', email.body)
        self.assertIn('Test body content', email.body)

        # Check HTML alternative
        html_content, _ = email.alternatives[0]  # type: ignore[attr-defined]
        self.assertIn('Test Notification', html_content)
        self.assertIn('Test body content', html_content)

    def test_subject_line_for_single_notification(self) -> None:
        """Test subject line format for single notification."""
        notification = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Custom Title Here',
            body='Some body',
            data={}
        )

        send_notification_email(self.user, [notification])

        email = mail.outbox[0]
        self.assertEqual(email.subject, 'SyncScript: Custom Title Here')

    def test_subject_line_for_multiple_notifications(self) -> None:
        """Test subject line format for multiple notifications."""
        notifications = [
            Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body=f'Body {i}',
                data={}
            )
            for i in range(5)
        ]

        send_notification_email(self.user, notifications)

        email = mail.outbox[0]
        self.assertEqual(email.subject, 'SyncScript: You have 5 new notifications')
