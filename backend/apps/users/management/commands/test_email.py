"""
Management command to test email configuration.

Usage:
    python manage.py test_email user@example.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, **options):
        recipient = options['recipient']

        self.stdout.write(self.style.WARNING(f'Testing email configuration...'))
        self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'SMTP User: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'Use SSL: {settings.EMAIL_USE_SSL}')
        self.stdout.write(f'Use TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To: {recipient}\n')

        try:
            send_mail(
                subject='SyncScript Email Test',
                message='This is a test email from SyncScript. If you receive this, your email configuration is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Test email sent successfully to {recipient}')
            )
            self.stdout.write(
                self.style.SUCCESS('Email configuration is working correctly!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send test email: {str(e)}')
            )
            raise CommandError(f'Email sending failed: {str(e)}')
