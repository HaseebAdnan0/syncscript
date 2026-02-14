from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime
from apps.sources.services import extract_metadata


class MetadataExtractionTests(TestCase):
    """Tests for metadata extraction service."""

    @patch('apps.sources.services.Article')
    def test_successful_extraction(self, mock_article_class: MagicMock) -> None:
        """Test successful metadata extraction returns all fields."""
        # Setup mock
        mock_article = MagicMock()
        mock_article.title = "Test Article Title"
        mock_article.authors = ["John Doe", "Jane Smith"]
        mock_article.publish_date = datetime(2024, 1, 15, 10, 30)
        mock_article.text = "This is a test article content. " * 50  # Long text
        mock_article_class.return_value = mock_article

        # Call function
        result = extract_metadata("https://example.com/article")

        # Assertions
        self.assertEqual(result['title'], "Test Article Title")
        self.assertEqual(result['authors'], ["John Doe", "Jane Smith"])
        self.assertEqual(result['publication_date'], "2024-01-15T10:30:00")
        self.assertEqual(len(result['abstract']), 500)
        self.assertIn('error', result.keys(), False)  # No error key

        # Verify Article was called correctly
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()

    @patch('apps.sources.services.Article')
    def test_timeout_handling(self, mock_article_class: MagicMock) -> None:
        """Test timeout during download returns fallback with error."""
        # Setup mock to raise timeout exception
        mock_article = MagicMock()
        mock_article.download.side_effect = TimeoutError("Connection timeout")
        mock_article_class.return_value = mock_article

        # Call function
        url = "https://slow-site.com/article"
        result = extract_metadata(url)

        # Assertions - should return fallback
        self.assertEqual(result['title'], url)
        self.assertIn('error', result)
        self.assertIn("Connection timeout", result['error'])

    @patch('apps.sources.services.Article')
    def test_invalid_url_handling(self, mock_article_class: MagicMock) -> None:
        """Test invalid URL returns fallback with error message."""
        # Setup mock to raise exception
        mock_article = MagicMock()
        mock_article.download.side_effect = ValueError("Invalid URL format")
        mock_article_class.return_value = mock_article

        # Call function
        url = "not-a-valid-url"
        result = extract_metadata(url)

        # Assertions
        self.assertEqual(result['title'], url)
        self.assertIn('error', result)
        self.assertIn("Invalid URL", result['error'])

    @patch('apps.sources.services.Article')
    def test_http_404_error(self, mock_article_class: MagicMock) -> None:
        """Test HTTP 404 error returns fallback."""
        # Setup mock to raise HTTP error
        mock_article = MagicMock()
        mock_article.download.side_effect = Exception("404 Not Found")
        mock_article_class.return_value = mock_article

        # Call function
        url = "https://example.com/nonexistent"
        result = extract_metadata(url)

        # Assertions
        self.assertEqual(result['title'], url)
        self.assertIn('error', result)
        self.assertIn("404", result['error'])

    @patch('apps.sources.services.Article')
    def test_http_500_error(self, mock_article_class: MagicMock) -> None:
        """Test HTTP 500 error returns fallback."""
        # Setup mock to raise server error
        mock_article = MagicMock()
        mock_article.download.side_effect = Exception("500 Internal Server Error")
        mock_article_class.return_value = mock_article

        # Call function
        url = "https://broken-site.com/article"
        result = extract_metadata(url)

        # Assertions
        self.assertEqual(result['title'], url)
        self.assertIn('error', result)
        self.assertIn("500", result['error'])

    @patch('apps.sources.services.Article')
    def test_empty_title_uses_url_fallback(self, mock_article_class: MagicMock) -> None:
        """Test when article has no title, url is used as fallback."""
        # Setup mock with empty title
        mock_article = MagicMock()
        mock_article.title = ""
        mock_article.authors = []
        mock_article.publish_date = None
        mock_article.text = "Some content here"
        mock_article_class.return_value = mock_article

        # Call function
        url = "https://example.com/no-title"
        result = extract_metadata(url)

        # Assertions
        self.assertEqual(result['title'], url)
        self.assertEqual(result['authors'], [])
        self.assertIsNone(result['publication_date'])
        self.assertEqual(result['abstract'], "Some content here")
