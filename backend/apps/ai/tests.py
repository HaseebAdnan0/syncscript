"""Tests for AI app functionality."""

from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.users.models import User
from apps.ai.services.usage import log_usage, get_daily_usage, get_remaining_requests
from apps.ai.models import AIUsageLog
from apps.ai.decorators import ai_rate_limit


class UsageTrackingTestCase(TestCase):
    """Test AI usage tracking service."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_log_usage(self):
        """Test logging AI usage."""
        log = log_usage(self.user, 'summary', 100)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.request_type, 'summary')
        self.assertEqual(log.tokens_used, 100)

    def test_get_daily_usage_empty(self):
        """Test getting daily usage when no usage exists."""
        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 0)
        self.assertEqual(usage['request_count'], 0)

    def test_get_daily_usage_with_logs(self):
        """Test getting daily usage with existing logs."""
        log_usage(self.user, 'summary', 100)
        log_usage(self.user, 'insights', 200)
        log_usage(self.user, 'question', 50)

        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 350)
        self.assertEqual(usage['request_count'], 3)

    def test_get_daily_usage_ignores_old_logs(self):
        """Test that daily usage only counts today's logs."""
        # Create an old log
        old_log = AIUsageLog.objects.create(
            user=self.user,
            request_type='summary',
            tokens_used=1000
        )
        old_log.created_at = datetime.now() - timedelta(days=2)
        old_log.save()

        # Create today's log
        log_usage(self.user, 'summary', 100)

        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 100)
        self.assertEqual(usage['request_count'], 1)

    def test_get_remaining_requests_full_allowance(self):
        """Test remaining requests with no usage."""
        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 20)  # Default limit

    def test_get_remaining_requests_partial_usage(self):
        """Test remaining requests with some usage."""
        for _ in range(5):
            log_usage(self.user, 'summary', 100)

        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 15)

    def test_get_remaining_requests_limit_exceeded(self):
        """Test remaining requests when limit is exceeded."""
        for _ in range(25):
            log_usage(self.user, 'summary', 100)

        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 0)


class RateLimitDecoratorTestCase(APITestCase):
    """Test AI rate limiting decorator."""

    def setUp(self):
        """Create test user and view."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create a test view wrapped with the decorator
        @api_view(['GET'])
        @ai_rate_limit
        def test_view(request):
            return Response({"message": "success"}, status=status.HTTP_200_OK)

        self.test_view = test_view

    def test_allows_request_within_limit(self):
        """Test that requests within limit are allowed."""
        # Create a mock request with force_authenticate
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'success')

    def test_blocks_request_at_limit(self):
        """Test that requests are blocked when limit is reached."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try one more request
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'AI request limit reached')

    def test_rate_limit_response_format(self):
        """Test that rate limit response has correct format."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try blocked request
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 429)

        # Check response format
        self.assertIn('error', response.data)
        self.assertIn('resets_at', response.data)
        self.assertIn('cached_available', response.data)
        self.assertEqual(response.data['cached_available'], True)

        # Verify resets_at is a valid ISO timestamp
        resets_at = response.data['resets_at']
        self.assertIsInstance(resets_at, str)
        # Should be parseable as datetime
        from datetime import datetime
        parsed = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
        self.assertIsNotNone(parsed)

    def test_rate_limit_resets_at_midnight(self):
        """Test that resets_at is tomorrow at midnight UTC."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try blocked request
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        resets_at_str = response.data['resets_at']

        # Parse the timestamp
        from datetime import datetime
        resets_at = datetime.fromisoformat(resets_at_str.replace('Z', '+00:00'))

        # Should be midnight
        self.assertEqual(resets_at.hour, 0)
        self.assertEqual(resets_at.minute, 0)
        self.assertEqual(resets_at.second, 0)

        # Should be tomorrow (or later today if it's currently before midnight)
        now = timezone.now()
        self.assertGreater(resets_at, now)


class ClaudeClientTestCase(TestCase):
    """Test Claude API client service."""

    def setUp(self):
        """Set up test fixtures."""
        from unittest.mock import Mock, MagicMock
        from apps.ai.services.claude_client import ClaudeClient

        # Mock the anthropic client
        self.mock_client = Mock()
        self.claude_client = ClaudeClient.__new__(ClaudeClient)
        self.claude_client.client = self.mock_client
        self.claude_client.model = "claude-3-5-sonnet-20241022"

    def test_summarize_success(self):
        """Test successful source summarization."""
        from unittest.mock import Mock

        # Mock response
        mock_message = Mock()
        mock_message.content = [Mock(text='{"abstract": "Test abstract", "key_findings": ["Finding 1"], "methodology": "Test method", "limitations": "Test limits", "keywords": ["keyword1"], "language": "en", "quality_flags": []}')]
        mock_message.usage = Mock(input_tokens=100, output_tokens=200)
        self.mock_client.messages.create.return_value = mock_message

        # Call summarize
        result = self.claude_client.summarize("Test content", "pdf")

        # Verify result
        self.assertEqual(result['abstract'], "Test abstract")
        self.assertEqual(result['key_findings'], ["Finding 1"])
        self.assertEqual(result['tokens_used'], 300)
        self.assertNotIn('error', result)

    def test_summarize_json_in_markdown(self):
        """Test summarize handles JSON in markdown code blocks."""
        from unittest.mock import Mock

        # Mock response with JSON in markdown
        mock_message = Mock()
        mock_message.content = [Mock(text='```json\n{"abstract": "Test", "key_findings": [], "methodology": "Test", "limitations": "None", "keywords": [], "language": "en", "quality_flags": []}\n```')]
        mock_message.usage = Mock(input_tokens=100, output_tokens=200)
        self.mock_client.messages.create.return_value = mock_message

        result = self.claude_client.summarize("Test content", "url")

        self.assertEqual(result['abstract'], "Test")
        self.assertEqual(result['tokens_used'], 300)

    def test_summarize_api_error(self):
        """Test summarize handles API errors gracefully."""
        # Mock API error by raising a generic exception
        self.mock_client.messages.create.side_effect = Exception("API error")

        result = self.claude_client.summarize("Test content", "pdf")

        self.assertIn('error', result)
        self.assertIn('Unexpected error', result['error'])
        self.assertEqual(result['tokens_used'], 0)

    def test_analyze_sources_success(self):
        """Test successful vault insights analysis."""
        from unittest.mock import Mock

        # Mock response
        mock_message = Mock()
        mock_message.content = [Mock(text='{"themes": [{"name": "Theme1", "weight": 0.8, "source_count": 3}], "research_gaps": ["Gap1"], "cross_references": [], "suggested_searches": ["search1"]}')]
        mock_message.usage = Mock(input_tokens=500, output_tokens=300)
        self.mock_client.messages.create.return_value = mock_message

        sources = [
            {"title": "Source 1", "authors": "Author A", "summary": "Summary 1", "url": "http://example.com/1"},
            {"title": "Source 2", "authors": "Author B", "summary": "Summary 2", "url": "http://example.com/2"}
        ]

        result = self.claude_client.analyze_sources(sources)

        self.assertEqual(len(result['themes']), 1)
        self.assertEqual(result['themes'][0]['name'], "Theme1")
        self.assertEqual(result['tokens_used'], 800)
        self.assertNotIn('error', result)

    def test_analyze_sources_handles_missing_fields(self):
        """Test analyze_sources handles sources with missing fields."""
        from unittest.mock import Mock

        mock_message = Mock()
        mock_message.content = [Mock(text='{"themes": [], "research_gaps": [], "cross_references": [], "suggested_searches": []}')]
        mock_message.usage = Mock(input_tokens=100, output_tokens=100)
        self.mock_client.messages.create.return_value = mock_message

        # Sources with missing fields
        sources = [
            {"title": "Source 1"},  # Missing authors, summary, url
            {},  # Empty source
        ]

        result = self.claude_client.analyze_sources(sources)

        # Should not raise error
        self.assertNotIn('error', result)
        self.assertEqual(result['tokens_used'], 200)

    def test_answer_question_success(self):
        """Test successful question answering with citations."""
        from unittest.mock import Mock

        mock_message = Mock()
        mock_message.content = [Mock(text='{"answer": "Test answer", "citations": [0, 1], "confidence": "high"}')]
        mock_message.usage = Mock(input_tokens=400, output_tokens=150)
        self.mock_client.messages.create.return_value = mock_message

        chunks = ["Chunk 0 content", "Chunk 1 content", "Chunk 2 content"]
        result = self.claude_client.answer_question("What is this about?", chunks)

        self.assertEqual(result['answer'], "Test answer")
        self.assertEqual(result['citations'], [0, 1])
        self.assertEqual(result['confidence'], "high")
        self.assertEqual(result['tokens_used'], 550)

    def test_answer_question_empty_context(self):
        """Test answer_question with empty context."""
        from unittest.mock import Mock

        mock_message = Mock()
        mock_message.content = [Mock(text='{"answer": "No context available", "citations": [], "confidence": "low"}')]
        mock_message.usage = Mock(input_tokens=50, output_tokens=30)
        self.mock_client.messages.create.return_value = mock_message

        result = self.claude_client.answer_question("What is this?", [])

        self.assertIn('answer', result)
        self.assertEqual(result['tokens_used'], 80)

    def test_client_initialization_requires_api_key(self):
        """Test that ClaudeClient raises error without API key."""
        from django.conf import settings
        from apps.ai.services.claude_client import ClaudeClient

        # Temporarily clear API key
        old_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        settings.ANTHROPIC_API_KEY = None

        with self.assertRaises(ValueError) as context:
            ClaudeClient()

        self.assertIn('ANTHROPIC_API_KEY not configured', str(context.exception))

        # Restore
        settings.ANTHROPIC_API_KEY = old_key


class ChunkingServiceTestCase(TestCase):
    """Test text chunking utilities."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        from apps.ai.services.chunking import chunk_text

        # Create a long text
        text = "This is sentence one. " * 200  # ~4400 chars
        chunks = chunk_text(text, max_tokens=500, overlap=50)

        # Should have multiple chunks
        self.assertGreater(len(chunks), 1)

        # Each chunk should have required fields
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('start_index', chunk)
            self.assertIn('end_index', chunk)
            self.assertIn('chunk_id', chunk)

        # Chunks should be sequential
        for i in range(len(chunks) - 1):
            self.assertLess(chunks[i]['start_index'], chunks[i + 1]['start_index'])

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        from apps.ai.services.chunking import chunk_text

        chunks = chunk_text("")
        self.assertEqual(len(chunks), 0)

        chunks = chunk_text("   ")
        self.assertEqual(len(chunks), 0)

    def test_chunk_text_short(self):
        """Test chunking text shorter than max_tokens."""
        from apps.ai.services.chunking import chunk_text

        text = "This is a short text."
        chunks = chunk_text(text, max_tokens=2000)

        # Should have exactly one chunk
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['text'], text)
        self.assertEqual(chunks[0]['chunk_id'], 0)

    def test_chunk_text_sentence_boundaries(self):
        """Test that chunks break at sentence boundaries when possible."""
        from apps.ai.services.chunking import chunk_text

        # Create text with clear sentences
        sentences = [f"Sentence number {i}." for i in range(100)]
        text = " ".join(sentences)

        chunks = chunk_text(text, max_tokens=200, overlap=20)

        # Most chunks should end with sentence punctuation
        ending_with_punctuation = sum(
            1 for chunk in chunks
            if chunk['text'][-1] in '.!?'
        )
        # Allow some flexibility but most should be sentence-aligned
        self.assertGreater(ending_with_punctuation, len(chunks) * 0.7)

    def test_chunk_text_overlap(self):
        """Test that chunks have proper overlap."""
        from apps.ai.services.chunking import chunk_text

        text = "Word " * 1000  # ~5000 chars
        chunks = chunk_text(text, max_tokens=500, overlap=100)

        if len(chunks) > 1:
            # Second chunk should start before first chunk ends (overlap)
            overlap_chars = 100 * 4  # overlap in characters
            expected_overlap_start = chunks[0]['end_index'] - overlap_chars

            # Allow some flexibility for sentence boundary adjustments
            self.assertLess(
                chunks[1]['start_index'],
                chunks[0]['end_index']
            )

    def test_get_relevant_chunks_keyword_matching(self):
        """Test chunk selection by keyword matching."""
        from apps.ai.services.chunking import get_relevant_chunks

        chunks = [
            {'text': 'Machine learning is a subset of artificial intelligence.', 'start_index': 0, 'end_index': 57, 'chunk_id': 0},
            {'text': 'Deep learning uses neural networks for pattern recognition.', 'start_index': 50, 'end_index': 110, 'chunk_id': 1},
            {'text': 'Python is a popular programming language.', 'start_index': 100, 'end_index': 142, 'chunk_id': 2},
            {'text': 'Machine learning algorithms can learn from data.', 'start_index': 140, 'end_index': 189, 'chunk_id': 3},
        ]

        # Question with keywords "machine learning"
        relevant = get_relevant_chunks("What is machine learning?", chunks, max_chunks=2)

        # Should return chunks with "machine learning"
        self.assertEqual(len(relevant), 2)
        self.assertIn('machine learning', relevant[0]['text'].lower())

    def test_get_relevant_chunks_empty_chunks(self):
        """Test get_relevant_chunks with empty chunks."""
        from apps.ai.services.chunking import get_relevant_chunks

        relevant = get_relevant_chunks("What is this?", [], max_chunks=5)
        self.assertEqual(len(relevant), 0)

    def test_get_relevant_chunks_empty_question(self):
        """Test get_relevant_chunks with empty question."""
        from apps.ai.services.chunking import get_relevant_chunks

        chunks = [
            {'text': 'Content 1', 'start_index': 0, 'end_index': 9, 'chunk_id': 0},
            {'text': 'Content 2', 'start_index': 9, 'end_index': 18, 'chunk_id': 1},
            {'text': 'Content 3', 'start_index': 18, 'end_index': 27, 'chunk_id': 2},
        ]

        # Should return first N chunks
        relevant = get_relevant_chunks("", chunks, max_chunks=2)
        self.assertEqual(len(relevant), 2)
        self.assertEqual(relevant[0]['chunk_id'], 0)
        self.assertEqual(relevant[1]['chunk_id'], 1)

    def test_get_relevant_chunks_respects_max_chunks(self):
        """Test that get_relevant_chunks respects max_chunks parameter."""
        from apps.ai.services.chunking import get_relevant_chunks

        chunks = [
            {'text': f'Chunk {i} with keyword test', 'start_index': i * 30, 'end_index': (i + 1) * 30, 'chunk_id': i}
            for i in range(10)
        ]

        relevant = get_relevant_chunks("test keyword", chunks, max_chunks=3)
        self.assertEqual(len(relevant), 3)

    def test_get_relevant_chunks_proximity_bonus(self):
        """Test that chunks with keywords close together score higher."""
        from apps.ai.services.chunking import get_relevant_chunks

        chunks = [
            {
                'text': 'Neural networks and deep learning are related concepts in machine learning.',
                'start_index': 0, 'end_index': 76, 'chunk_id': 0
            },
            {
                'text': 'Neural networks are important. Deep learning is also important.',
                'start_index': 70, 'end_index': 133, 'chunk_id': 1
            },
            {
                'text': 'This text mentions neural at the start and learning at the end of a very long sentence.',
                'start_index': 130, 'end_index': 218, 'chunk_id': 2
            },
        ]

        # Question with "neural learning"
        relevant = get_relevant_chunks("neural learning", chunks, max_chunks=2)

        # First chunk has both keywords close together, should rank higher
        self.assertEqual(relevant[0]['chunk_id'], 0)
