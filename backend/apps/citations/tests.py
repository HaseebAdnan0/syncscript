"""Tests for citations app"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.citations.services.doi_lookup import normalize_doi, fetch_doi_metadata


class DOILookupTests(TestCase):
    """Tests for DOI metadata lookup service"""

    def test_normalize_doi_plain(self):
        """Test normalizing plain DOI"""
        doi = "10.1234/example"
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1234/example")

    def test_normalize_doi_with_url(self):
        """Test normalizing DOI from doi.org URL"""
        doi = "https://doi.org/10.1234/example"
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1234/example")

    def test_normalize_doi_with_dx_url(self):
        """Test normalizing DOI from dx.doi.org URL"""
        doi = "http://dx.doi.org/10.1234/example"
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1234/example")

    def test_normalize_doi_partial_url(self):
        """Test normalizing DOI from partial URL"""
        doi = "doi.org/10.1234/example"
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1234/example")

    def test_normalize_doi_complex(self):
        """Test normalizing complex DOI with multiple dots and slashes"""
        doi = "10.1000/182.123/abc"
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1000/182.123/abc")

    def test_normalize_doi_invalid(self):
        """Test normalizing invalid DOI returns None"""
        self.assertIsNone(normalize_doi("not-a-doi"))
        self.assertIsNone(normalize_doi(""))
        self.assertIsNone(normalize_doi("9.1234/example"))  # Must start with 10.

    def test_normalize_doi_with_whitespace(self):
        """Test normalizing DOI with whitespace"""
        doi = "  10.1234/example  "
        result = normalize_doi(doi)
        self.assertEqual(result, "10.1234/example")

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_success(self, mock_get_publication):
        """Test successful DOI metadata fetch"""
        # Mock CrossRef API response
        mock_get_publication.return_value = {
            'title': ['Test Article Title'],
            'author': [
                {'given': 'John', 'family': 'Doe'},
                {'given': 'Jane', 'family': 'Smith'},
            ],
            'published': {
                'date-parts': [[2024, 1, 15]]
            },
            'container-title': ['Journal of Testing'],
            'volume': '42',
            'issue': '3',
            'page': '123-145',
            'publisher': 'Test Publisher',
        }

        result = fetch_doi_metadata("10.1234/test")

        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test Article Title')
        self.assertEqual(result['authors'], ['Doe, John', 'Smith, Jane'])
        self.assertEqual(result['publication_date'], '2024-01-15')
        self.assertEqual(result['journal'], 'Journal of Testing')
        self.assertEqual(result['volume'], '42')
        self.assertEqual(result['issue'], '3')
        self.assertEqual(result['pages'], '123-145')
        self.assertEqual(result['publisher'], 'Test Publisher')
        self.assertEqual(result['doi'], '10.1234/test')

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_minimal(self, mock_get_publication):
        """Test DOI metadata fetch with minimal data"""
        mock_get_publication.return_value = {
            'title': ['Minimal Article'],
            # No authors, dates, or other fields
        }

        result = fetch_doi_metadata("10.1234/minimal")

        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Minimal Article')
        self.assertEqual(result['authors'], ['Unknown'])
        self.assertEqual(result['publication_date'], 'n.d.')
        self.assertEqual(result['journal'], '')
        self.assertEqual(result['volume'], '')
        self.assertEqual(result['issue'], '')
        self.assertEqual(result['pages'], '')
        self.assertEqual(result['publisher'], '')

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_no_title(self, mock_get_publication):
        """Test DOI metadata fetch fails without title"""
        mock_get_publication.return_value = {
            'author': [{'given': 'John', 'family': 'Doe'}],
            # No title - should fail
        }

        result = fetch_doi_metadata("10.1234/notitle")
        self.assertIsNone(result)

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_api_error(self, mock_get_publication):
        """Test DOI metadata fetch returns None on API error"""
        # Simulate API error
        mock_get_publication.side_effect = Exception("API Error")

        result = fetch_doi_metadata("10.1234/error")
        self.assertIsNone(result)

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_not_found(self, mock_get_publication):
        """Test DOI metadata fetch returns None when DOI not found"""
        mock_get_publication.return_value = None

        result = fetch_doi_metadata("10.9999/notfound")
        self.assertIsNone(result)

    def test_fetch_doi_metadata_invalid_doi(self):
        """Test fetch with invalid DOI returns None"""
        result = fetch_doi_metadata("not-a-doi")
        self.assertIsNone(result)

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_author_family_only(self, mock_get_publication):
        """Test DOI metadata with authors having only family name"""
        mock_get_publication.return_value = {
            'title': ['Test Article'],
            'author': [
                {'family': 'Doe'},  # No given name
                {'given': 'Jane', 'family': 'Smith'},
            ],
        }

        result = fetch_doi_metadata("10.1234/test")

        self.assertIsNotNone(result)
        self.assertEqual(result['authors'], ['Doe', 'Smith, Jane'])

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_created_date_fallback(self, mock_get_publication):
        """Test DOI metadata uses created date when published not available"""
        mock_get_publication.return_value = {
            'title': ['Test Article'],
            'created': {
                'date-parts': [[2023, 5, 20]]
            },
            # No 'published' field
        }

        result = fetch_doi_metadata("10.1234/test")

        self.assertIsNotNone(result)
        self.assertEqual(result['publication_date'], '2023-05-20')

    @patch('apps.citations.services.doi_lookup.get_publication_as_json')
    def test_fetch_doi_metadata_year_only_date(self, mock_get_publication):
        """Test DOI metadata with year-only publication date"""
        mock_get_publication.return_value = {
            'title': ['Test Article'],
            'published': {
                'date-parts': [[2024]]  # Only year
            },
        }

        result = fetch_doi_metadata("10.1234/test")

        self.assertIsNotNone(result)
        self.assertEqual(result['publication_date'], '2024-01-01')
