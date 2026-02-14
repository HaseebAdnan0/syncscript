"""Tests for daily and weekly digest email tasks"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from apps.notifications.models import Notification, NotificationPreferences
from apps.notifications.tasks import send_daily_digest, send_weekly_digest

User = get_user_model()


class DailyDigestTaskTestCase(TestCase):
    """Test cases for send_daily_digest task"""

    def setUp(self):
        """Create test users and notifications"""
        # User with daily preference and un-emailed notifications
        self.user1 = User.objects.create_user(username='daily_user', email='daily@test.com')
        self.user1_prefs = NotificationPreferences.objects.get(user=self.user1)
        self.user1_prefs.email_digest_frequency = 'daily'
        self.user1_prefs.save()

        self.notif1 = Notification.objects.create(
            user=self.user1,
            type='vault_invite',
            title='Test Notification 1',
            body='Body 1',
            data={}
        )
        self.notif2 = Notification.objects.create(
            user=self.user1,
            type='source_added',
            title='Test Notification 2',
            body='Body 2',
            data={}
        )

        # User with daily preference but no notifications
        self.user2 = User.objects.create_user(username='daily_no_notifs', email='daily2@test.com')
        self.user2_prefs = NotificationPreferences.objects.get(user=self.user2)
        self.user2_prefs.email_digest_frequency = 'daily'
        self.user2_prefs.save()

        # User with weekly preference (should be ignored by daily task)
        self.user3 = User.objects.create_user(username='weekly_user', email='weekly@test.com')
        self.user3_prefs = NotificationPreferences.objects.get(user=self.user3)
        self.user3_prefs.email_digest_frequency = 'weekly'
        self.user3_prefs.save()

        Notification.objects.create(
            user=self.user3,
            type='vault_invite',
            title='Weekly Notification',
            body='Body',
            data={}
        )

    def test_sends_digest_to_daily_users(self):
        """Test that digest is sent to users with daily preference"""
        sent_count = send_daily_digest()

        # Should send to user1 only (user2 has no notifications, user3 is weekly)
        self.assertEqual(sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'daily@test.com')

    def test_batches_multiple_notifications(self):
        """Test that multiple notifications are batched into one email"""
        send_daily_digest()

        # Should send one email with both notifications
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertIn('Test Notification 1', email_body)
        self.assertIn('Test Notification 2', email_body)

    def test_marks_notifications_as_emailed(self):
        """Test that notifications are marked as emailed after sending"""
        send_daily_digest()

        # Refresh from DB
        self.notif1.refresh_from_db()
        self.notif2.refresh_from_db()

        # Both should be marked as emailed
        self.assertIsNotNone(self.notif1.emailed_at)
        self.assertIsNotNone(self.notif2.emailed_at)

    def test_skips_already_emailed_notifications(self):
        """Test that already emailed notifications are not included"""
        # Mark notif1 as already emailed
        self.notif1.emailed_at = timezone.now()
        self.notif1.save()

        send_daily_digest()

        # Should send one email with only notif2
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertNotIn('Test Notification 1', email_body)
        self.assertIn('Test Notification 2', email_body)

    def test_skips_users_with_no_notifications(self):
        """Test that users with no un-emailed notifications are skipped"""
        # user2 has daily preference but no notifications
        sent_count = send_daily_digest()

        # Should only send to user1
        self.assertEqual(sent_count, 1)

    def test_ignores_other_frequencies(self):
        """Test that users with other frequency preferences are ignored"""
        # user3 has weekly preference
        send_daily_digest()

        # Should not send to user3
        for email in mail.outbox:
            self.assertNotEqual(email.to[0], 'weekly@test.com')

    def test_returns_zero_when_no_users(self):
        """Test that zero is returned when no users need digest"""
        # Change all users to non-daily
        self.user1_prefs.email_digest_frequency = 'immediate'
        self.user1_prefs.save()
        self.user2_prefs.email_digest_frequency = 'none'
        self.user2_prefs.save()

        sent_count = send_daily_digest()

        self.assertEqual(sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)


class WeeklyDigestTaskTestCase(TestCase):
    """Test cases for send_weekly_digest task"""

    def setUp(self):
        """Create test users and notifications"""
        # User with weekly preference and un-emailed notifications
        self.user1 = User.objects.create_user(username='weekly_user', email='weekly@test.com')
        self.user1_prefs = NotificationPreferences.objects.get(user=self.user1)
        self.user1_prefs.email_digest_frequency = 'weekly'
        self.user1_prefs.save()

        self.notif1 = Notification.objects.create(
            user=self.user1,
            type='vault_invite',
            title='Test Notification 1',
            body='Body 1',
            data={}
        )
        self.notif2 = Notification.objects.create(
            user=self.user1,
            type='source_added',
            title='Test Notification 2',
            body='Body 2',
            data={}
        )
        self.notif3 = Notification.objects.create(
            user=self.user1,
            type='mention',
            title='Test Notification 3',
            body='Body 3',
            data={}
        )

        # User with daily preference (should be ignored by weekly task)
        self.user2 = User.objects.create_user(username='daily_user', email='daily@test.com')
        self.user2_prefs = NotificationPreferences.objects.get(user=self.user2)
        self.user2_prefs.email_digest_frequency = 'daily'
        self.user2_prefs.save()

        Notification.objects.create(
            user=self.user2,
            type='vault_invite',
            title='Daily Notification',
            body='Body',
            data={}
        )

    def test_sends_digest_to_weekly_users(self):
        """Test that digest is sent to users with weekly preference"""
        sent_count = send_weekly_digest()

        # Should send to user1 only (user2 is daily)
        self.assertEqual(sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'weekly@test.com')

    def test_batches_multiple_notifications(self):
        """Test that all notifications are batched into one email"""
        send_weekly_digest()

        # Should send one email with all three notifications
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertIn('Test Notification 1', email_body)
        self.assertIn('Test Notification 2', email_body)
        self.assertIn('Test Notification 3', email_body)

    def test_marks_notifications_as_emailed(self):
        """Test that notifications are marked as emailed after sending"""
        send_weekly_digest()

        # Refresh from DB
        self.notif1.refresh_from_db()
        self.notif2.refresh_from_db()
        self.notif3.refresh_from_db()

        # All should be marked as emailed
        self.assertIsNotNone(self.notif1.emailed_at)
        self.assertIsNotNone(self.notif2.emailed_at)
        self.assertIsNotNone(self.notif3.emailed_at)

    def test_skips_already_emailed_notifications(self):
        """Test that already emailed notifications are not included"""
        # Mark notif1 and notif2 as already emailed
        now = timezone.now()
        self.notif1.emailed_at = now
        self.notif1.save()
        self.notif2.emailed_at = now
        self.notif2.save()

        send_weekly_digest()

        # Should send one email with only notif3
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertNotIn('Test Notification 1', email_body)
        self.assertNotIn('Test Notification 2', email_body)
        self.assertIn('Test Notification 3', email_body)

    def test_ignores_other_frequencies(self):
        """Test that users with other frequency preferences are ignored"""
        # user2 has daily preference
        send_weekly_digest()

        # Should not send to user2
        for email in mail.outbox:
            self.assertNotEqual(email.to[0], 'daily@test.com')

    def test_returns_zero_when_no_users(self):
        """Test that zero is returned when no users need digest"""
        # Change user to non-weekly
        self.user1_prefs.email_digest_frequency = 'immediate'
        self.user1_prefs.save()

        sent_count = send_weekly_digest()

        self.assertEqual(sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)
