"""
Management command to seed test data for SyncScript.
Creates test users, vaults, sources, annotations, and notifications.

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --flush  # Clear existing data first
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Clear existing test data before seeding',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.flush_test_data()

        self.stdout.write(self.style.NOTICE('Seeding test data...'))

        # Create users
        users = self.create_users()

        # Create vaults
        vaults = self.create_vaults(users)

        # Create sources
        sources = self.create_sources(vaults, users)

        # Create annotations
        self.create_annotations(sources, users)

        # Create notifications
        self.create_notifications(users, vaults)

        # Create AI usage logs
        self.create_ai_usage(users)

        self.stdout.write(self.style.SUCCESS('Test data seeded successfully!'))
        self.print_summary(users)

    def flush_test_data(self):
        """Remove existing test data."""
        self.stdout.write(self.style.WARNING('Flushing existing test data...'))

        test_emails = [
            'admin@syncscript.test',
            'alice@syncscript.test',
            'bob@syncscript.test',
            'charlie@syncscript.test',
            'diana@syncscript.test',
        ]

        deleted_count = User.objects.filter(email__in=test_emails).delete()[0]
        self.stdout.write(f'  Deleted {deleted_count} test users and related data')

    def create_users(self):
        """Create test user accounts."""
        self.stdout.write('  Creating test users...')

        users = {}
        password = 'TestPass123!'

        # Admin user
        admin, created = User.objects.get_or_create(
            email='admin@syncscript.test',
            defaults={
                'username': 'admin_test',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True,
                'institution': 'SyncScript',
                'bio': 'Platform administrator',
                'onboarding_completed': True,
                'onboarding_path': 'skipped',
            }
        )
        if created:
            admin.set_password(password)
            admin.save()
        users['admin'] = admin

        # Alice - Main researcher
        alice, created = User.objects.get_or_create(
            email='alice@syncscript.test',
            defaults={
                'username': 'alice_researcher',
                'first_name': 'Alice',
                'last_name': 'Research',
                'email_verified': True,
                'institution': 'MIT',
                'bio': 'AI/ML researcher focusing on natural language processing',
                'default_citation_format': 'apa7',
                'onboarding_completed': True,
                'onboarding_path': 'guided',
            }
        )
        if created:
            alice.set_password(password)
            alice.save()
        users['alice'] = alice

        # Bob - Collaborator
        bob, created = User.objects.get_or_create(
            email='bob@syncscript.test',
            defaults={
                'username': 'bob_collab',
                'first_name': 'Bob',
                'last_name': 'Collaborator',
                'email_verified': True,
                'institution': 'Stanford',
                'bio': 'Climate science researcher',
                'default_citation_format': 'chicago17',
                'onboarding_completed': True,
                'onboarding_path': 'demo',
            }
        )
        if created:
            bob.set_password(password)
            bob.save()
        users['bob'] = bob

        # Charlie - Viewer
        charlie, created = User.objects.get_or_create(
            email='charlie@syncscript.test',
            defaults={
                'username': 'charlie_viewer',
                'first_name': 'Charlie',
                'last_name': 'Viewer',
                'email_verified': True,
                'institution': 'Berkeley',
                'bio': 'Graduate student',
                'onboarding_completed': True,
                'onboarding_path': 'skipped',
            }
        )
        if created:
            charlie.set_password(password)
            charlie.save()
        users['charlie'] = charlie

        # Diana - New user (for onboarding tests)
        diana, created = User.objects.get_or_create(
            email='diana@syncscript.test',
            defaults={
                'username': 'diana_new',
                'first_name': 'Diana',
                'last_name': 'Newuser',
                'email_verified': True,
                'institution': 'Harvard',
                'bio': '',
                'onboarding_completed': False,
                'onboarding_step': 'welcome',
            }
        )
        if created:
            diana.set_password(password)
            diana.save()
        users['diana'] = diana

        self.stdout.write(f'    Created/updated {len(users)} users')
        return users

    def create_vaults(self, users):
        """Create test vaults with memberships."""
        self.stdout.write('  Creating test vaults...')

        from apps.vaults.models import Vault, VaultMembership, RoleChoices

        vaults = {}

        # AI Research Papers vault (Alice owns, Bob contributes, Charlie views)
        ai_vault, created = Vault.objects.get_or_create(
            name='AI Research Papers 2025',
            owner=users['alice'],
            defaults={
                'description': 'Collection of cutting-edge AI/ML research papers from 2025. '
                               'Focus on transformers, LLMs, and multimodal systems.',
                'default_citation_format': 'ieee',
            }
        )
        vaults['ai_research'] = ai_vault

        if created:
            # Add members
            VaultMembership.objects.get_or_create(
                vault=ai_vault,
                user=users['alice'],
                defaults={'role': RoleChoices.OWNER, 'added_by': users['alice']}
            )
            VaultMembership.objects.get_or_create(
                vault=ai_vault,
                user=users['bob'],
                defaults={'role': RoleChoices.CONTRIBUTOR, 'added_by': users['alice']}
            )
            VaultMembership.objects.get_or_create(
                vault=ai_vault,
                user=users['charlie'],
                defaults={'role': RoleChoices.VIEWER, 'added_by': users['alice']}
            )

        # Climate Science vault (Bob owns, private)
        climate_vault, created = Vault.objects.get_or_create(
            name='Climate Science Review',
            owner=users['bob'],
            defaults={
                'description': 'Climate change research and data analysis papers.',
                'default_citation_format': 'apa7',
            }
        )
        vaults['climate'] = climate_vault

        if created:
            VaultMembership.objects.get_or_create(
                vault=climate_vault,
                user=users['bob'],
                defaults={'role': RoleChoices.OWNER, 'added_by': users['bob']}
            )

        # Empty vault (for testing empty states)
        empty_vault, created = Vault.objects.get_or_create(
            name='Empty Test Vault',
            owner=users['alice'],
            defaults={
                'description': 'A vault with no sources for testing empty states.',
            }
        )
        vaults['empty'] = empty_vault

        if created:
            VaultMembership.objects.get_or_create(
                vault=empty_vault,
                user=users['alice'],
                defaults={'role': RoleChoices.OWNER, 'added_by': users['alice']}
            )

        self.stdout.write(f'    Created/updated {len(vaults)} vaults')
        return vaults

    def create_sources(self, vaults, users):
        """Create test sources in vaults."""
        self.stdout.write('  Creating test sources...')

        from apps.sources.models import Source, SourceType

        sources = []

        # AI Research Papers vault sources
        ai_sources_data = [
            {
                'url': 'https://arxiv.org/abs/2303.08774',
                'title': 'GPT-4 Technical Report',
                'description': 'Technical report describing GPT-4, a large-scale multimodal model.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['OpenAI'],
                    'year': 2023,
                    'arxiv_id': '2303.08774',
                },
            },
            {
                'url': 'https://arxiv.org/abs/2302.13971',
                'title': 'LLaMA: Open and Efficient Foundation Language Models',
                'description': 'A collection of foundation language models ranging from 7B to 65B parameters.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['Hugo Touvron', 'Thibaut Lavril', 'et al.'],
                    'year': 2023,
                    'arxiv_id': '2302.13971',
                },
            },
            {
                'url': 'https://arxiv.org/abs/2307.09288',
                'title': 'Llama 2: Open Foundation and Fine-Tuned Chat Models',
                'description': 'Llama 2 family of pretrained and fine-tuned LLMs at 7B, 13B, and 70B parameters.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['Hugo Touvron', 'Louis Martin', 'et al.'],
                    'year': 2023,
                    'arxiv_id': '2307.09288',
                },
            },
            {
                'url': 'https://arxiv.org/abs/2305.10403',
                'title': 'Tree of Thoughts: Deliberate Problem Solving with LLMs',
                'description': 'A framework for language model inference that enables exploration over coherent text.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['Shunyu Yao', 'Dian Yu', 'et al.'],
                    'year': 2023,
                    'arxiv_id': '2305.10403',
                },
            },
            {
                'url': 'https://www.nature.com/articles/s41586-021-03819-2',
                'title': 'Highly accurate protein structure prediction with AlphaFold',
                'description': 'AlphaFold predicts protein structures with atomic accuracy.',
                'source_type': SourceType.JOURNAL,
                'metadata': {
                    'authors': ['John Jumper', 'et al.'],
                    'year': 2021,
                    'journal': 'Nature',
                    'doi': '10.1038/s41586-021-03819-2',
                },
            },
        ]

        for source_data in ai_sources_data:
            source, _ = Source.objects.get_or_create(
                vault=vaults['ai_research'],
                url=source_data['url'],
                defaults={
                    'title': source_data['title'],
                    'description': source_data['description'],
                    'source_type': source_data['source_type'],
                    'metadata': source_data['metadata'],
                    'created_by': users['alice'],
                }
            )
            sources.append(source)

        # Climate vault sources
        climate_sources_data = [
            {
                'url': 'https://www.ipcc.ch/report/ar6/wg1/',
                'title': 'IPCC AR6 Working Group I Report',
                'description': 'The Physical Science Basis of Climate Change.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['IPCC'],
                    'year': 2021,
                },
            },
            {
                'url': 'https://www.nature.com/articles/s41558-020-0883-0',
                'title': 'Climate tipping points — too risky to bet against',
                'description': 'Analysis of potential climate tipping points and their interactions.',
                'source_type': SourceType.JOURNAL,
                'metadata': {
                    'authors': ['Timothy Lenton', 'et al.'],
                    'year': 2020,
                    'journal': 'Nature',
                },
            },
            {
                'url': 'https://arxiv.org/abs/2101.00027',
                'title': 'Machine Learning for Climate Science',
                'description': 'Survey of ML applications in climate modeling and prediction.',
                'source_type': SourceType.URL,
                'metadata': {
                    'authors': ['Various'],
                    'year': 2021,
                },
            },
        ]

        for source_data in climate_sources_data:
            source, _ = Source.objects.get_or_create(
                vault=vaults['climate'],
                url=source_data['url'],
                defaults={
                    'title': source_data['title'],
                    'description': source_data['description'],
                    'source_type': source_data['source_type'],
                    'metadata': source_data['metadata'],
                    'created_by': users['bob'],
                }
            )
            sources.append(source)

        self.stdout.write(f'    Created/updated {len(sources)} sources')
        return sources

    def create_annotations(self, sources, users):
        """Create test annotations with threaded replies."""
        self.stdout.write('  Creating test annotations...')

        from apps.annotations.models import Annotation

        annotation_count = 0

        # Only annotate if we have sources
        if not sources:
            return

        # Annotations on first AI source (GPT-4)
        gpt4_source = sources[0] if sources else None
        if gpt4_source:
            ann1, created = Annotation.objects.get_or_create(
                source=gpt4_source,
                user=users['alice'],
                content='Key finding: GPT-4 exhibits human-level performance on various professional exams.',
                defaults={
                    'page_number': 1,
                    'position': {'x': 100, 'y': 200},
                }
            )
            if created:
                annotation_count += 1

                # Reply from Bob
                reply1 = Annotation.objects.create(
                    source=gpt4_source,
                    user=users['bob'],
                    content='Interesting! But we should note the benchmark saturation concerns.',
                    parent=ann1,
                )
                annotation_count += 1

                # Alice's response to Bob
                Annotation.objects.create(
                    source=gpt4_source,
                    user=users['alice'],
                    content='Good point. The paper does address this in section 4.2.',
                    parent=ann1,
                )
                annotation_count += 1

            # Another annotation on same source
            ann2, created = Annotation.objects.get_or_create(
                source=gpt4_source,
                user=users['bob'],
                content='The multimodal capabilities are impressive. See Figure 3 for examples.',
                defaults={
                    'page_number': 5,
                    'position': {'x': 150, 'y': 300},
                }
            )
            if created:
                annotation_count += 1

        # Annotations on LLaMA source
        llama_source = sources[1] if len(sources) > 1 else None
        if llama_source:
            ann3, created = Annotation.objects.get_or_create(
                source=llama_source,
                user=users['alice'],
                content='Open-source alternative to GPT models. Important for reproducibility!',
                defaults={
                    'page_number': 1,
                }
            )
            if created:
                annotation_count += 1

            ann4, created = Annotation.objects.get_or_create(
                source=llama_source,
                user=users['charlie'],
                content='How does this compare to GPT-3.5 in practice?',
                defaults={
                    'page_number': 3,
                }
            )
            if created:
                annotation_count += 1
                # Alice replies
                Annotation.objects.create(
                    source=llama_source,
                    user=users['alice'],
                    content='See Table 2 - competitive on most benchmarks with 65B variant.',
                    parent=ann4,
                )
                annotation_count += 1

        self.stdout.write(f'    Created {annotation_count} annotations')

    def create_notifications(self, users, vaults):
        """Create test notifications."""
        self.stdout.write('  Creating test notifications...')

        from apps.notifications.models import Notification

        notifications_data = [
            {
                'user': users['alice'],
                'type': 'source_added',
                'title': 'New source added',
                'body': 'Bob added "Climate tipping points" to Climate Science Review',
                'data': {'vault_id': str(vaults['climate'].id)},
            },
            {
                'user': users['bob'],
                'type': 'vault_invite',
                'title': 'Vault invitation',
                'body': 'Alice invited you to "AI Research Papers 2025" as Contributor',
                'data': {'vault_id': str(vaults['ai_research'].id)},
                'read_at': timezone.now() - timedelta(days=1),  # Already read
            },
            {
                'user': users['charlie'],
                'type': 'annotation_reply',
                'title': 'New reply to your annotation',
                'body': 'Alice replied to your comment on "LLaMA: Open and Efficient..."',
                'data': {'vault_id': str(vaults['ai_research'].id)},
            },
            {
                'user': users['alice'],
                'type': 'member_joined',
                'title': 'New member joined',
                'body': 'Charlie joined "AI Research Papers 2025" as Viewer',
                'data': {'vault_id': str(vaults['ai_research'].id)},
                'read_at': timezone.now(),  # Already read
            },
            {
                'user': users['diana'],
                'type': 'vault_invite',
                'title': 'Vault invitation',
                'body': 'Alice invited you to collaborate on "AI Research Papers 2025"',
                'data': {'vault_id': str(vaults['ai_research'].id)},
            },
        ]

        created_count = 0
        for notif_data in notifications_data:
            _, created = Notification.objects.get_or_create(
                user=notif_data['user'],
                title=notif_data['title'],
                defaults={
                    'type': notif_data['type'],
                    'body': notif_data['body'],
                    'data': notif_data['data'],
                    'read_at': notif_data.get('read_at'),
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'    Created {created_count} notifications')

    def create_ai_usage(self, users):
        """Create sample AI usage logs."""
        self.stdout.write('  Creating AI usage logs...')

        from apps.ai.models import AIUsageLog, RequestType

        # Give Alice some usage history
        usage_data = [
            {'user': users['alice'], 'request_type': RequestType.SUMMARY, 'tokens_used': 1500},
            {'user': users['alice'], 'request_type': RequestType.SUMMARY, 'tokens_used': 1200},
            {'user': users['alice'], 'request_type': RequestType.INSIGHTS, 'tokens_used': 3500},
            {'user': users['alice'], 'request_type': RequestType.QUESTION, 'tokens_used': 800},
            {'user': users['bob'], 'request_type': RequestType.SUMMARY, 'tokens_used': 1800},
            {'user': users['bob'], 'request_type': RequestType.QUESTION, 'tokens_used': 950},
        ]

        # Only create if no recent usage exists
        recent_usage = AIUsageLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exists()

        if not recent_usage:
            for usage in usage_data:
                AIUsageLog.objects.create(**usage)
            self.stdout.write(f'    Created {len(usage_data)} AI usage logs')
        else:
            self.stdout.write('    Skipped (recent usage exists)')

    def print_summary(self, users):
        """Print summary of test accounts."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('TEST ACCOUNTS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Password for all accounts: TestPass123!')
        self.stdout.write('')
        self.stdout.write(f'  {"Email":<30} {"Role":<15} {"Notes"}')
        self.stdout.write(f'  {"-" * 30} {"-" * 15} {"-" * 30}')

        accounts = [
            ('admin@syncscript.test', 'Admin', 'Superuser, admin access'),
            ('alice@syncscript.test', 'Researcher', 'Owns AI vault, completed onboarding'),
            ('bob@syncscript.test', 'Collaborator', 'Contributor to AI vault, owns Climate vault'),
            ('charlie@syncscript.test', 'Viewer', 'Viewer on AI vault'),
            ('diana@syncscript.test', 'New User', 'Fresh account, onboarding incomplete'),
        ]

        for email, role, notes in accounts:
            self.stdout.write(f'  {email:<30} {role:<15} {notes}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
