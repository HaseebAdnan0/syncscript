"""Tests for citations app"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.citations.services.doi_lookup import normalize_doi, fetch_doi_metadata
from apps.citations.services.isbn_lookup import normalize_isbn, fetch_isbn_metadata
from apps.citations.services.structured_citation import (
    has_complete_metadata,
    generate_structured_citation,
)
from apps.citations.services.ai_citation import (
    generate_ai_citation,
    _build_system_prompt,
    _build_user_prompt,
    _parse_response,
)
from apps.citations.models import CitationFormat


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
        assert result is not None  # Type narrowing
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
        assert result is not None  # Type narrowing
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
        assert result is not None  # Type narrowing
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
        assert result is not None  # Type narrowing
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
        assert result is not None  # Type narrowing
        self.assertEqual(result['publication_date'], '2024-01-01')


class ISBNLookupTests(TestCase):
    """Tests for ISBN metadata lookup service"""

    def test_normalize_isbn_10_plain(self):
        """Test normalizing plain ISBN-10"""
        isbn = "0123456789"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "0123456789")

    def test_normalize_isbn_10_with_hyphens(self):
        """Test normalizing ISBN-10 with hyphens"""
        isbn = "0-123-45678-9"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "0123456789")

    def test_normalize_isbn_10_with_x(self):
        """Test normalizing ISBN-10 with X check digit"""
        isbn = "012345678X"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "012345678X")

    def test_normalize_isbn_13_plain(self):
        """Test normalizing plain ISBN-13"""
        isbn = "9780123456789"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "9780123456789")

    def test_normalize_isbn_13_with_hyphens(self):
        """Test normalizing ISBN-13 with hyphens"""
        isbn = "978-0-123-45678-9"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "9780123456789")

    def test_normalize_isbn_13_979_prefix(self):
        """Test normalizing ISBN-13 with 979 prefix"""
        isbn = "979-0-123-45678-6"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "9790123456786")

    def test_normalize_isbn_with_spaces(self):
        """Test normalizing ISBN with spaces"""
        isbn = "978 0 123 45678 9"
        result = normalize_isbn(isbn)
        self.assertEqual(result, "9780123456789")

    def test_normalize_isbn_invalid(self):
        """Test normalizing invalid ISBN returns None"""
        self.assertIsNone(normalize_isbn("not-an-isbn"))
        self.assertIsNone(normalize_isbn(""))
        self.assertIsNone(normalize_isbn("123"))  # Too short
        self.assertIsNone(normalize_isbn("9770123456789"))  # Wrong prefix

    def test_normalize_isbn_with_whitespace(self):
        """Test normalizing ISBN with whitespace"""
        isbn = "  978-0-123-45678-9  "
        result = normalize_isbn(isbn)
        self.assertEqual(result, "9780123456789")

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_success(self, mock_urlopen):
        """Test successful ISBN metadata fetch"""
        # Mock OpenLibrary API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "ISBN:9780123456789": {
                "title": "Test Book Title",
                "authors": [
                    {"name": "John Doe"},
                    {"name": "Jane Smith"}
                ],
                "publish_date": "January 15, 2024",
                "publishers": [{"name": "Test Publisher"}],
                "number_of_pages": 350,
                "identifiers": {
                    "isbn_10": ["0123456789"],
                    "isbn_13": ["9780123456789"]
                }
            }
        }'''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("9780123456789")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing
        self.assertEqual(result['title'], 'Test Book Title')
        self.assertEqual(result['authors'], ['John Doe', 'Jane Smith'])
        self.assertEqual(result['publication_date'], '2024')
        self.assertEqual(result['publisher'], 'Test Publisher')
        self.assertEqual(result['pages'], 350)
        self.assertEqual(result['isbn_10'], '0123456789')
        self.assertEqual(result['isbn_13'], '9780123456789')

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_minimal(self, mock_urlopen):
        """Test ISBN metadata fetch with minimal data"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "ISBN:9780123456789": {
                "title": "Minimal Book"
            }
        }'''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("9780123456789")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing
        self.assertEqual(result['title'], 'Minimal Book')
        self.assertEqual(result['authors'], ['Unknown'])
        self.assertEqual(result['publication_date'], 'n.d.')
        self.assertEqual(result['publisher'], '')
        self.assertEqual(result['pages'], 0)

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_no_title(self, mock_urlopen):
        """Test ISBN metadata fetch fails without title"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "ISBN:9780123456789": {
                "authors": [{"name": "John Doe"}]
            }
        }'''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("9780123456789")
        self.assertIsNone(result)

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_not_found(self, mock_urlopen):
        """Test ISBN metadata fetch returns None when ISBN not found"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("9999999999999")
        self.assertIsNone(result)

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_api_error(self, mock_urlopen):
        """Test ISBN metadata fetch returns None on API error"""
        # Simulate API error
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("API Error")

        result = fetch_isbn_metadata("9780123456789")
        self.assertIsNone(result)

    def test_fetch_isbn_metadata_invalid_isbn(self):
        """Test fetch with invalid ISBN returns None"""
        result = fetch_isbn_metadata("not-an-isbn")
        self.assertIsNone(result)

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_isbn_10(self, mock_urlopen):
        """Test ISBN metadata fetch with ISBN-10"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "ISBN:0123456789": {
                "title": "Test Book",
                "identifiers": {
                    "isbn_10": ["0123456789"],
                    "isbn_13": ["9780123456789"]
                }
            }
        }'''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("0123456789")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing
        self.assertEqual(result['isbn_10'], '0123456789')
        self.assertEqual(result['isbn_13'], '9780123456789')

    @patch('apps.citations.services.isbn_lookup.urllib.request.urlopen')
    def test_fetch_isbn_metadata_publisher_string(self, mock_urlopen):
        """Test ISBN metadata with publisher as string instead of dict"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "ISBN:9780123456789": {
                "title": "Test Book",
                "publishers": ["Test Publisher"]
            }
        }'''
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_isbn_metadata("9780123456789")

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing
        self.assertEqual(result['publisher'], 'Test Publisher')


class StructuredCitationTests(TestCase):
    """Tests for structured citation generation service"""

    def test_has_complete_metadata_valid(self):
        """Test metadata completeness check with valid data"""
        metadata = {
            'title': 'Test Article',
            'authors': ['John Doe', 'Jane Smith'],
            'publication_date': '2024',
        }
        self.assertTrue(has_complete_metadata(metadata))

    def test_has_complete_metadata_missing_title(self):
        """Test metadata completeness check fails without title"""
        metadata = {
            'authors': ['John Doe'],
            'publication_date': '2024',
        }
        self.assertFalse(has_complete_metadata(metadata))

    def test_has_complete_metadata_empty_title(self):
        """Test metadata completeness check fails with empty title"""
        metadata = {
            'title': '   ',
            'authors': ['John Doe'],
            'publication_date': '2024',
        }
        self.assertFalse(has_complete_metadata(metadata))

    def test_has_complete_metadata_missing_authors(self):
        """Test metadata completeness check fails without authors"""
        metadata = {
            'title': 'Test Article',
            'publication_date': '2024',
        }
        self.assertFalse(has_complete_metadata(metadata))

    def test_has_complete_metadata_empty_authors(self):
        """Test metadata completeness check fails with empty authors list"""
        metadata = {
            'title': 'Test Article',
            'authors': [],
            'publication_date': '2024',
        }
        self.assertFalse(has_complete_metadata(metadata))

    def test_has_complete_metadata_missing_date(self):
        """Test metadata completeness check fails without date"""
        metadata = {
            'title': 'Test Article',
            'authors': ['John Doe'],
        }
        self.assertFalse(has_complete_metadata(metadata))

    def test_has_complete_metadata_with_author_key(self):
        """Test metadata completeness accepts 'author' instead of 'authors'"""
        metadata = {
            'title': 'Test Article',
            'author': 'John Doe',
            'date': '2024',
        }
        self.assertTrue(has_complete_metadata(metadata))

    def test_has_complete_metadata_with_year_key(self):
        """Test metadata completeness accepts 'year' instead of 'publication_date'"""
        metadata = {
            'title': 'Test Article',
            'authors': ['John Doe'],
            'year': '2024',
        }
        self.assertTrue(has_complete_metadata(metadata))

    def test_generate_bibtex_article(self):
        """Test BibTeX generation for journal article"""
        metadata = {
            'title': 'Machine Learning in Healthcare',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024-01-15',
            'journal': 'Journal of AI Research',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
            'doi': '10.1234/example',
        }

        citation = generate_structured_citation(metadata, CitationFormat.BIBTEX, 'smith2024')

        self.assertIn('@article{smith2024,', citation)
        self.assertIn('title = {Machine Learning in Healthcare}', citation)
        self.assertIn('author = {Smith, John and Doe, Jane}', citation)
        self.assertIn('year = {2024}', citation)
        self.assertIn('journal = {Journal of AI Research}', citation)
        self.assertIn('volume = {10}', citation)
        self.assertIn('number = {2}', citation)
        self.assertIn('pages = {123-145}', citation)
        self.assertIn('doi = {10.1234/example}', citation)

    def test_generate_bibtex_book(self):
        """Test BibTeX generation for book"""
        metadata = {
            'title': 'Deep Learning Fundamentals',
            'authors': ['Brown, Alice'],
            'publication_date': '2024',
            'publisher': 'MIT Press',
            'edition': '2nd',
            'isbn': '9780123456789',
        }

        citation = generate_structured_citation(metadata, CitationFormat.BIBTEX, 'brown2024')

        self.assertIn('@book{brown2024,', citation)
        self.assertIn('title = {Deep Learning Fundamentals}', citation)
        self.assertIn('author = {Brown, Alice}', citation)
        self.assertIn('year = {2024}', citation)
        self.assertIn('publisher = {MIT Press}', citation)
        self.assertIn('edition = {2nd}', citation)
        self.assertIn('isbn = {9780123456789}', citation)

    def test_generate_bibtex_web_source(self):
        """Test BibTeX generation for web source"""
        metadata = {
            'title': 'Introduction to Python',
            'authors': ['Python Foundation'],
            'publication_date': '2024',
            'url': 'https://python.org/docs/intro',
        }

        citation = generate_structured_citation(metadata, CitationFormat.BIBTEX, 'python2024')

        self.assertIn('@misc{python2024,', citation)
        self.assertIn('title = {Introduction to Python}', citation)
        self.assertIn('url = {https://python.org/docs/intro}', citation)

    @patch('apps.citations.services.structured_citation.CitationStylesBibliography')
    @patch('apps.citations.services.structured_citation.CitationStylesStyle')
    @patch('apps.citations.services.structured_citation._get_style_file')
    def test_generate_apa7_citation(self, mock_get_style, mock_style, mock_bib):
        """Test APA 7th edition citation generation"""
        # Mock style file path
        mock_get_style.return_value = '/fake/path/apa-7th-edition.csl'

        # Mock bibliography output
        mock_bib_instance = MagicMock()
        mock_bib_instance.bibliography.return_value = ['Smith, J., & Doe, J. (2024). Test article. <i>Journal</i>, <i>10</i>(2), 123-145.']
        mock_bib.return_value = mock_bib_instance

        metadata = {
            'title': 'Test article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024',
            'journal': 'Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
        }

        citation = generate_structured_citation(metadata, CitationFormat.APA7)

        self.assertIn('Smith, J., & Doe, J. (2024)', citation)
        mock_get_style.assert_called_once_with(CitationFormat.APA7)

    @patch('apps.citations.services.structured_citation.CitationStylesBibliography')
    @patch('apps.citations.services.structured_citation.CitationStylesStyle')
    @patch('apps.citations.services.structured_citation._get_style_file')
    def test_generate_mla9_citation(self, mock_get_style, mock_style, mock_bib):
        """Test MLA 9th edition citation generation"""
        mock_get_style.return_value = '/fake/path/mla9.csl'
        mock_bib_instance = MagicMock()
        mock_bib_instance.bibliography.return_value = ['Smith, John, and Jane Doe. "Test Article." <i>Journal</i>, vol. 10, no. 2, 2024, pp. 123-145.']
        mock_bib.return_value = mock_bib_instance

        metadata = {
            'title': 'Test Article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024',
            'journal': 'Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
        }

        citation = generate_structured_citation(metadata, CitationFormat.MLA9)

        self.assertIn('Smith, John', citation)
        mock_get_style.assert_called_once_with(CitationFormat.MLA9)

    @patch('apps.citations.services.structured_citation.CitationStylesBibliography')
    @patch('apps.citations.services.structured_citation.CitationStylesStyle')
    @patch('apps.citations.services.structured_citation._get_style_file')
    def test_generate_chicago_citation(self, mock_get_style, mock_style, mock_bib):
        """Test Chicago 17th edition citation generation"""
        mock_get_style.return_value = '/fake/path/chicago.csl'
        mock_bib_instance = MagicMock()
        mock_bib_instance.bibliography.return_value = ['Smith, John, and Jane Doe. 2024. "Test Article." <i>Journal</i> 10 (2): 123-145.']
        mock_bib.return_value = mock_bib_instance

        metadata = {
            'title': 'Test Article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024',
            'journal': 'Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
        }

        citation = generate_structured_citation(metadata, CitationFormat.CHICAGO17)

        self.assertIn('2024', citation)
        mock_get_style.assert_called_once_with(CitationFormat.CHICAGO17)

    @patch('apps.citations.services.structured_citation.CitationStylesBibliography')
    @patch('apps.citations.services.structured_citation.CitationStylesStyle')
    @patch('apps.citations.services.structured_citation._get_style_file')
    def test_generate_ieee_citation(self, mock_get_style, mock_style, mock_bib):
        """Test IEEE citation generation"""
        mock_get_style.return_value = '/fake/path/ieee.csl'
        mock_bib_instance = MagicMock()
        mock_bib_instance.bibliography.return_value = ['J. Smith and J. Doe, "Test article," <i>Journal</i>, vol. 10, no. 2, pp. 123-145, 2024.']
        mock_bib.return_value = mock_bib_instance

        metadata = {
            'title': 'Test article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024',
            'journal': 'Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
        }

        citation = generate_structured_citation(metadata, CitationFormat.IEEE)

        self.assertIn('J. Smith', citation)
        mock_get_style.assert_called_once_with(CitationFormat.IEEE)

    @patch('apps.citations.services.structured_citation.CitationStylesBibliography')
    @patch('apps.citations.services.structured_citation.CitationStylesStyle')
    @patch('apps.citations.services.structured_citation._get_style_file')
    def test_generate_harvard_citation(self, mock_get_style, mock_style, mock_bib):
        """Test Harvard citation generation"""
        mock_get_style.return_value = '/fake/path/harvard.csl'
        mock_bib_instance = MagicMock()
        mock_bib_instance.bibliography.return_value = ['Smith, J. and Doe, J. (2024) "Test article", <i>Journal</i>, 10(2), pp. 123-145.']
        mock_bib.return_value = mock_bib_instance

        metadata = {
            'title': 'Test article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024',
            'journal': 'Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
        }

        citation = generate_structured_citation(metadata, CitationFormat.HARVARD)

        self.assertIn('Smith, J.', citation)
        mock_get_style.assert_called_once_with(CitationFormat.HARVARD)

    def test_generate_citation_incomplete_metadata(self):
        """Test citation generation fails with incomplete metadata"""
        metadata = {
            'title': 'Test Article',
            # Missing authors and date
        }

        with self.assertRaises(ValueError) as cm:
            generate_structured_citation(metadata, CitationFormat.APA7)

        self.assertIn('Incomplete metadata', str(cm.exception))

    def test_generate_citation_with_doi(self):
        """Test citation generation includes DOI"""
        metadata = {
            'title': 'Test Article',
            'authors': ['Smith, John'],
            'publication_date': '2024',
            'doi': '10.1234/example',
        }

        citation = generate_structured_citation(metadata, CitationFormat.BIBTEX)

        self.assertIn('doi = {10.1234/example}', citation)

    def test_generate_citation_with_url(self):
        """Test citation generation includes URL"""
        metadata = {
            'title': 'Web Article',
            'authors': ['Smith, John'],
            'publication_date': '2024',
            'url': 'https://example.com/article',
        }

        citation = generate_structured_citation(metadata, CitationFormat.BIBTEX)

        self.assertIn('url = {https://example.com/article}', citation)


class AICitationTests(TestCase):
    """Tests for AI-powered citation generation"""

    def test_parse_response_with_split(self):
        """Test parsing response with separator"""
        response = """Smith, J. (2024). Test article.
---SPLIT---
Smith, J. (2024). <i>Test article</i>."""

        plain, html = _parse_response(response)

        self.assertEqual(plain, "Smith, J. (2024). Test article.")
        self.assertEqual(html, "Smith, J. (2024). <i>Test article</i>.")

    def test_parse_response_without_split(self):
        """Test parsing response without separator (fallback)"""
        response = "Smith, J. (2024). Test article."

        plain, html = _parse_response(response)

        self.assertEqual(plain, "Smith, J. (2024). Test article.")
        self.assertEqual(html, "Smith, J. (2024). Test article.")

    def test_build_system_prompt_apa7(self):
        """Test building APA7 system prompt"""
        prompt = _build_system_prompt(CitationFormat.APA7)

        self.assertIn("APA 7th Edition", prompt)
        self.assertIn("Author, A. A. (Year)", prompt)
        self.assertIn("---SPLIT---", prompt)
        self.assertIn("n.d.", prompt)

    def test_build_system_prompt_mla9(self):
        """Test building MLA9 system prompt"""
        prompt = _build_system_prompt(CitationFormat.MLA9)

        self.assertIn("MLA 9th Edition", prompt)
        self.assertIn("quotation marks", prompt)
        self.assertIn("---SPLIT---", prompt)

    def test_build_system_prompt_bibtex(self):
        """Test building BibTeX system prompt"""
        prompt = _build_system_prompt(CitationFormat.BIBTEX)

        self.assertIn("BibTeX", prompt)
        self.assertIn("@article", prompt)
        self.assertIn("@book", prompt)
        self.assertIn("@misc", prompt)

    def test_build_user_prompt_complete_metadata(self):
        """Test building user prompt with complete metadata"""
        source_data = {
            'title': 'Test Article',
            'url': 'https://example.com/article',
            'authors': ['Smith, John', 'Doe, Jane'],
            'metadata': {
                'journal': 'Nature',
                'volume': '123',
                'issue': '4',
                'pages': '567-589',
                'publication_date': '2024',
                'doi': '10.1234/example',
            }
        }

        prompt = _build_user_prompt(source_data, CitationFormat.APA7)

        self.assertIn("Test Article", prompt)
        self.assertIn("Smith, John, Doe, Jane", prompt)
        self.assertIn("Nature", prompt)
        self.assertIn("123", prompt)
        self.assertIn("10.1234/example", prompt)
        self.assertIn("---SPLIT---", prompt)

    def test_build_user_prompt_incomplete_metadata(self):
        """Test building user prompt with missing fields"""
        source_data = {
            'title': 'Untitled Source',
            'url': 'https://example.com',
        }

        prompt = _build_user_prompt(source_data, CitationFormat.MLA9)

        self.assertIn("Untitled Source", prompt)
        self.assertIn("Not provided", prompt)

    def test_build_user_prompt_authors_as_string(self):
        """Test building user prompt with authors as string"""
        source_data = {
            'title': 'Test',
            'authors': 'Smith, John',
        }

        prompt = _build_user_prompt(source_data, CitationFormat.APA7)

        self.assertIn("Smith, John", prompt)

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('apps.citations.services.ai_citation.Anthropic')
    def test_generate_ai_citation_apa7(self, mock_anthropic):
        """Test generating APA7 citation with Claude"""
        # Mock Claude API response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """Smith, J. (2024). Test article. Nature, 123(4), 567-589.
---SPLIT---
Smith, J. (2024). Test article. <i>Nature</i>, <i>123</i>(4), 567-589."""
        mock_message.content = [mock_content]
        mock_message.usage = MagicMock(input_tokens=150, output_tokens=50)
        mock_message.model = 'claude-3-5-sonnet-20241022'

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        source_data = {
            'title': 'Test article',
            'authors': ['Smith, John'],
            'metadata': {
                'journal': 'Nature',
                'volume': '123',
                'issue': '4',
                'pages': '567-589',
                'publication_date': '2024',
            }
        }

        plain, html, usage_data = generate_ai_citation(source_data, CitationFormat.APA7)

        self.assertIn("Smith, J. (2024)", plain)
        self.assertIn("<i>Nature</i>", html)
        self.assertNotIn("<i>", plain)

        # Verify usage data
        self.assertEqual(usage_data['input_tokens'], 150)
        self.assertEqual(usage_data['output_tokens'], 50)
        self.assertEqual(usage_data['total_tokens'], 200)
        self.assertEqual(usage_data['model'], 'claude-3-5-sonnet-20241022')

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs['model'], 'claude-3-5-sonnet-20241022')
        self.assertIn('APA 7th Edition', call_kwargs['system'])

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('apps.citations.services.ai_citation.Anthropic')
    def test_generate_ai_citation_bibtex(self, mock_anthropic):
        """Test generating BibTeX citation with Claude"""
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """@article{Smith2024Test,
  author = {Smith, John},
  title = {Test Article},
  journal = {Nature},
  year = {2024}
}
---SPLIT---
@article{Smith2024Test,
  author = {Smith, John},
  title = {Test Article},
  journal = {Nature},
  year = {2024}
}"""
        mock_message.content = [mock_content]
        mock_message.usage = MagicMock(input_tokens=120, output_tokens=40)
        mock_message.model = 'claude-3-5-sonnet-20241022'

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        source_data = {
            'title': 'Test Article',
            'authors': ['Smith, John'],
            'metadata': {
                'journal': 'Nature',
                'publication_date': '2024',
            }
        }

        plain, html, _usage_data = generate_ai_citation(source_data, CitationFormat.BIBTEX)

        self.assertIn("@article{Smith2024Test", plain)
        self.assertIn("author = {Smith, John}", plain)

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_ai_citation_missing_api_key(self):
        """Test error when ANTHROPIC_API_KEY is not set"""
        source_data = {
            'title': 'Test',
            'authors': ['Smith'],
        }

        with self.assertRaises(ValueError) as cm:
            generate_ai_citation(source_data, CitationFormat.APA7)

        self.assertIn("ANTHROPIC_API_KEY", str(cm.exception))

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('apps.citations.services.ai_citation.Anthropic')
    def test_generate_ai_citation_incomplete_metadata(self, mock_anthropic):
        """Test AI citation handles incomplete metadata gracefully"""
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """Unknown. (n.d.). Untitled source. Retrieved February 14, 2026 from https://example.com
---SPLIT---
Unknown. (n.d.). Untitled source. Retrieved February 14, 2026 from https://example.com"""
        mock_message.content = [mock_content]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=30)
        mock_message.model = 'claude-3-5-sonnet-20241022'

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        source_data = {
            'title': 'Untitled source',
            'url': 'https://example.com',
        }

        plain, html, _usage_data = generate_ai_citation(source_data, CitationFormat.APA7)

        self.assertIn("Unknown", plain)
        self.assertIn("n.d.", plain)
        self.assertIn("example.com", plain)


class CitationEndpointTests(TestCase):
    """Tests for citation generation API endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source

        User = get_user_model()

        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123'
        )

        # Create vault owned by user1
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for citations',
            owner=self.user1
        )

        # Create source with complete metadata
        self.source_complete = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Complete Article',
            metadata={
                'authors': ['Smith, John', 'Doe, Jane'],
                'publication_date': '2024',
                'journal': 'Test Journal',
                'volume': '10',
                'issue': '2',
                'pages': '123-145',
            },
            created_by=self.user1
        )

        # Create source with incomplete metadata
        self.source_incomplete = Source.objects.create(
            vault=self.vault,
            url='https://example.com/web',
            title='Web Article',
            metadata={},
            created_by=self.user1
        )

    def test_generate_citation_structured(self):
        """Test generating citation with complete metadata (structured)"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user1)

        response = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'bibtex'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('citation', data)
        self.assertIn('citation_html', data)
        self.assertEqual(data['format'], 'bibtex')
        self.assertEqual(data['source'], 'structured')
        self.assertEqual(data['cached'], False)

        # Verify citation content
        self.assertIn('@', data['citation'])
        self.assertIn('Smith, John', data['citation'])

    @patch('apps.citations.tasks.generate_ai_citation_task.delay')
    def test_generate_citation_ai(self, mock_task_delay):
        """Test generating citation with incomplete metadata (AI) - now async"""
        from rest_framework.test import APIClient

        # Mock Celery task
        mock_result = MagicMock()
        mock_result.id = '12345678-1234-1234-1234-123456789abc'
        mock_task_delay.return_value = mock_result

        client = APIClient()
        client.force_authenticate(user=self.user1)

        response = client.post(
            f'/api/v1/citations/sources/{self.source_incomplete.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        # Now returns 202 Accepted with task_id (async)
        self.assertEqual(response.status_code, 202)
        data = response.json()

        self.assertIn('task_id', data)
        self.assertIn('status_url', data)
        self.assertEqual(data['task_id'], '12345678-1234-1234-1234-123456789abc')

    def test_generate_citation_caching(self):
        """Test citation caching"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user1)

        # First request generates citation
        response1 = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'bibtex'},
            format='json'
        )

        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertEqual(data1['cached'], False)

        # Second request should use cache
        response2 = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'bibtex'},
            format='json'
        )

        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2['cached'], True)
        self.assertEqual(data1['citation'], data2['citation'])

    def test_generate_citation_unauthenticated(self):
        """Test generating citation without authentication"""
        from rest_framework.test import APIClient

        client = APIClient()

        response = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 401)

    def test_generate_citation_no_permission(self):
        """Test generating citation without vault access"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user2)

        response = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_generate_citation_invalid_format(self):
        """Test generating citation with invalid format"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user1)

        response = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'invalid'},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

    def test_generate_citation_source_not_found(self):
        """Test generating citation for non-existent source"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user1)

        response = client.post(
            '/api/v1/citations/sources/99999/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 404)

    def test_generate_citation_with_vault_member(self):
        """Test generating citation as vault member (viewer)"""
        from rest_framework.test import APIClient
        from apps.vaults.models import VaultMembership, RoleChoices

        # Add user2 as viewer
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.user2,
            role=RoleChoices.VIEWER
        )

        client = APIClient()
        client.force_authenticate(user=self.user2)

        response = client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'bibtex'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('citation', data)


class CitationCacheInvalidationTests(TestCase):
    """Tests for citation cache invalidation via signals and utilities"""

    def setUp(self):
        """Set up test fixtures"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source

        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.vault = Vault.objects.create(
            name='Test Vault',
            owner=self.user
        )
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            metadata={
                'authors': 'Smith, J.',
                'publication_date': '2024',
                'journal': 'Test Journal'
            },
            created_by=self.user
        )

    def test_invalidate_citation_cache_utility(self):
        """Test invalidate_citation_cache utility function removes citations"""
        from apps.citations.utils import invalidate_citation_cache

        # Add cached citation
        self.source.metadata['citations'] = {
            'apa7': {
                'text': 'Smith, J. (2024). Test Article.',
                'html': 'Smith, J. (2024). <i>Test Article</i>.',
                'generated_at': '2024-01-01T00:00:00',
                'source': 'structured'
            }
        }
        self.source.save()

        # Reload source to verify cache was saved
        self.source.refresh_from_db()
        self.assertIn('citations', self.source.metadata)

        # Invalidate cache
        invalidate_citation_cache(self.source)

        # Reload and verify citations removed
        self.source.refresh_from_db()
        self.assertNotIn('citations', self.source.metadata)

    def test_invalidate_citation_cache_empty_metadata(self):
        """Test invalidate_citation_cache handles source with empty metadata gracefully"""
        from apps.citations.utils import invalidate_citation_cache

        # Create source with empty metadata dict
        self.source.metadata = {}
        self.source.save()

        # Should not raise error
        invalidate_citation_cache(self.source)

    def test_invalidate_citation_cache_no_citations(self):
        """Test invalidate_citation_cache handles source with no citations key gracefully"""
        from apps.citations.utils import invalidate_citation_cache

        # Source has metadata but no citations
        self.source.metadata = {'some_key': 'some_value'}
        self.source.save()

        # Should not raise error
        invalidate_citation_cache(self.source)

        # Metadata should still exist
        self.source.refresh_from_db()
        self.assertEqual(self.source.metadata, {'some_key': 'some_value'})

    def test_signal_invalidates_cache_on_metadata_change(self):
        """Test that signal invalidates cache when source metadata is updated"""
        # Add cached citation
        self.source.metadata['citations'] = {
            'apa7': {
                'text': 'Smith, J. (2024). Test Article.',
                'html': 'Smith, J. (2024). <i>Test Article</i>.',
                'generated_at': '2024-01-01T00:00:00',
                'source': 'structured'
            }
        }
        self.source.save()

        # Reload source to verify cache was saved
        self.source.refresh_from_db()
        self.assertIn('citations', self.source.metadata)

        # Update metadata (trigger signal)
        self.source.metadata['authors'] = 'Doe, J.'
        self.source.save()

        # Reload and verify citations were invalidated
        self.source.refresh_from_db()
        self.assertNotIn('citations', self.source.metadata)

    def test_signal_does_not_invalidate_cache_on_other_field_change(self):
        """Test that signal does NOT invalidate cache when non-metadata fields change"""
        # Add cached citation to existing metadata (don't replace the whole dict)
        self.source.metadata['citations'] = {
            'apa7': {
                'text': 'Smith, J. (2024). Test Article.',
                'html': 'Smith, J. (2024). <i>Test Article</i>.',
                'generated_at': '2024-01-01T00:00:00',
                'source': 'structured'
            }
        }
        self.source.save()

        # Reload source
        self.source.refresh_from_db()
        self.assertIn('citations', self.source.metadata)

        # Update title (not metadata, so signal should not trigger cache invalidation)
        self.source.title = 'Updated Title'
        self.source.save()

        # Reload and verify citations still exist
        self.source.refresh_from_db()
        self.assertIn('citations', self.source.metadata)

    def test_signal_does_not_trigger_on_new_source(self):
        """Test that signal does not trigger on source creation"""
        from apps.sources.models import Source

        # Create new source with metadata and citations
        new_source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/new-article',
            title='New Article',
            metadata={
                'authors': 'Johnson, K.',
                'citations': {
                    'apa7': {
                        'text': 'Johnson, K. (2024). New Article.',
                        'html': 'Johnson, K. (2024). <i>New Article</i>.',
                        'generated_at': '2024-01-01T00:00:00',
                        'source': 'structured'
                    }
                }
            },
            created_by=self.user
        )

        # Reload and verify citations were NOT invalidated (signal should not run on create)
        new_source.refresh_from_db()
        self.assertIn('citations', new_source.metadata)


class AsyncCitationTaskTests(TestCase):
    """Tests for async citation generation via Celery tasks"""

    def setUp(self):
        """Set up test data"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source

        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test description',
            owner=self.user
        )

        self.source = Source.objects.create(
            title='Test Source',
            url='https://example.com/article',
            vault=self.vault,
            created_by=self.user,
            metadata={
                'title': 'Test Article'
                # Incomplete metadata (no authors/date) to trigger AI citation
            }
        )

    @patch('apps.citations.tasks.generate_ai_citation')
    def test_generate_ai_citation_task_success(self, mock_ai_citation):
        """Test successful async AI citation generation"""
        from apps.citations.tasks import generate_ai_citation_task

        # Mock AI citation service with usage data
        mock_ai_citation.return_value = (
            'Test, A. (2024). Test Article.',
            'Test, A. (2024). <i>Test Article</i>.',
            {'input_tokens': 150, 'output_tokens': 50, 'total_tokens': 200, 'model': 'claude-3-5-sonnet-20241022'}
        )

        # Run task synchronously (not via .delay()) with user_id
        result = generate_ai_citation_task(self.source.id, 'apa7', self.user.id)

        # Verify result structure
        self.assertEqual(result['source_id'], self.source.id)
        self.assertEqual(result['format'], 'apa7')
        self.assertEqual(result['citation'], 'Test, A. (2024). Test Article.')
        self.assertEqual(result['citation_html'], 'Test, A. (2024). <i>Test Article</i>.')
        self.assertFalse(result['cached'])

        # Verify citation was cached in source metadata
        self.source.refresh_from_db()
        self.assertIn('citations', self.source.metadata)
        self.assertIn('apa7', self.source.metadata['citations'])
        cached = self.source.metadata['citations']['apa7']
        self.assertEqual(cached['text'], 'Test, A. (2024). Test Article.')
        self.assertEqual(cached['html'], 'Test, A. (2024). <i>Test Article</i>.')
        self.assertEqual(cached['source'], 'ai')

    @patch('apps.citations.tasks.generate_ai_citation')
    def test_generate_ai_citation_task_different_formats(self, mock_ai_citation):
        """Test task handles different citation formats"""
        from apps.citations.tasks import generate_ai_citation_task

        # Mock AI citation service with usage data
        mock_ai_citation.return_value = (
            'Test. "Article." Journal.',
            'Test. "Article." <i>Journal</i>.',
            {'input_tokens': 120, 'output_tokens': 40, 'total_tokens': 160, 'model': 'claude-3-5-sonnet-20241022'}
        )

        # Generate BibTeX citation with user_id
        result = generate_ai_citation_task(self.source.id, 'bibtex', self.user.id)

        self.assertEqual(result['format'], 'bibtex')
        self.assertIn('Test. "Article." Journal.', result['citation'])

        # Verify BibTeX was cached
        self.source.refresh_from_db()
        self.assertIn('bibtex', self.source.metadata['citations'])

    @patch('apps.citations.tasks.generate_ai_citation')
    def test_generate_ai_citation_task_api_error(self, mock_ai_citation):
        """Test task handles API errors and retries"""
        from apps.citations.tasks import generate_ai_citation_task

        # Mock API error
        mock_ai_citation.side_effect = Exception("API error")

        # Task should raise the original exception (wrapped in Retry) with user_id
        with self.assertRaises(Exception):
            generate_ai_citation_task(self.source.id, 'apa7', self.user.id)

    def test_generate_ai_citation_task_source_not_found(self):
        """Test task handles non-existent source"""
        from apps.citations.tasks import generate_ai_citation_task
        from django.http import Http404

        # Non-existent source ID with user_id
        with self.assertRaises(Http404):
            generate_ai_citation_task(99999, 'apa7', self.user.id)


class AIUsageLoggingTests(TestCase):
    """Tests for AI citation usage logging (US-010)"""

    def setUp(self):
        """Set up test data"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source

        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        self.vault = Vault.objects.create(
            name='Test Vault',
            owner=self.user
        )

        self.source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            url='https://example.com/test',
            source_type='URL',
            created_by=self.user
        )

    def test_log_ai_citation_usage(self):
        """Test logging AI citation usage creates audit log"""
        from apps.citations.utils import log_ai_citation_usage
        from apps.vaults.models import AuditLog

        usage_data = {
            'input_tokens': 150,
            'output_tokens': 50,
            'total_tokens': 200,
            'model': 'claude-3-5-sonnet-20241022'
        }

        audit_log = log_ai_citation_usage(
            self.user,
            self.vault,
            self.source,
            'apa7',
            usage_data
        )

        # Verify audit log was created
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.vault, self.vault)
        self.assertEqual(audit_log.actor, self.user)
        self.assertEqual(audit_log.action, 'AI_CITATION_GENERATED')

        # Verify metadata
        self.assertEqual(audit_log.metadata['source_id'], self.source.id)
        self.assertEqual(audit_log.metadata['source_title'], 'Test Source')
        self.assertEqual(audit_log.metadata['format'], 'apa7')
        self.assertEqual(audit_log.metadata['input_tokens'], 150)
        self.assertEqual(audit_log.metadata['output_tokens'], 50)
        self.assertEqual(audit_log.metadata['total_tokens'], 200)
        self.assertEqual(audit_log.metadata['model_used'], 'claude-3-5-sonnet-20241022')

        # Verify in database
        logs = AuditLog.objects.filter(action='AI_CITATION_GENERATED')
        self.assertEqual(logs.count(), 1)

    @patch('apps.citations.tasks.generate_ai_citation')
    def test_task_logs_ai_usage(self, mock_ai_citation):
        """Test that the Celery task logs AI usage"""
        from apps.citations.tasks import generate_ai_citation_task
        from apps.vaults.models import AuditLog

        # Mock AI citation service with usage data
        mock_ai_citation.return_value = (
            'Test, A. (2024). Test Article.',
            'Test, A. (2024). <i>Test Article</i>.',
            {
                'input_tokens': 175,
                'output_tokens': 60,
                'total_tokens': 235,
                'model': 'claude-3-5-sonnet-20241022'
            }
        )

        # Run task
        generate_ai_citation_task(self.source.id, 'mla9', self.user.id)

        # Verify audit log was created
        logs = AuditLog.objects.filter(action='AI_CITATION_GENERATED')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.vault, self.vault)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.metadata['format'], 'mla9')
        self.assertEqual(log.metadata['input_tokens'], 175)
        self.assertEqual(log.metadata['output_tokens'], 60)
        self.assertEqual(log.metadata['total_tokens'], 235)

    def test_log_usage_with_missing_usage_fields(self):
        """Test logging handles missing usage data fields gracefully"""
        from apps.citations.utils import log_ai_citation_usage
        from apps.vaults.models import AuditLog

        # Missing fields in usage data
        usage_data = {
            'model': 'claude-3-5-sonnet-20241022'
            # input_tokens, output_tokens, total_tokens missing
        }

        audit_log = log_ai_citation_usage(
            self.user,
            self.vault,
            self.source,
            'bibtex',
            usage_data
        )

        # Verify defaults to 0 for missing token counts
        self.assertEqual(audit_log.metadata['input_tokens'], 0)
        self.assertEqual(audit_log.metadata['output_tokens'], 0)
        self.assertEqual(audit_log.metadata['total_tokens'], 0)
        self.assertEqual(audit_log.metadata['model_used'], 'claude-3-5-sonnet-20241022')


class AsyncCitationEndpointTests(TestCase):
    """Tests for async citation generation endpoints"""

    def setUp(self):
        """Set up test data"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from rest_framework.test import APIClient

        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test description',
            owner=self.user
        )

        self.source_incomplete = Source.objects.create(
            title='Incomplete Source',
            url='https://example.com/article',
            vault=self.vault,
            created_by=self.user,
            metadata={
                'title': 'Test Article'
                # No authors/date - incomplete metadata to trigger async
            }
        )

        self.source_complete = Source.objects.create(
            title='Complete Source',
            url='https://example.com/article2',
            vault=self.vault,
            created_by=self.user,
            metadata={
                'title': 'Complete Article',
                'authors': ['Smith, John', 'Doe, Jane'],
                'publication_date': '2024-01-15',
                'journal': 'Test Journal'
            }
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.citations.tasks.generate_ai_citation_task.delay')
    def test_incomplete_metadata_returns_202_with_task_id(self, mock_task_delay):
        """Test endpoint returns 202 Accepted for incomplete metadata (async AI)"""
        # Mock Celery task
        mock_result = MagicMock()
        task_id = '12345678-1234-1234-1234-123456789abc'
        mock_result.id = task_id
        mock_task_delay.return_value = mock_result

        response = self.client.post(
            f'/api/v1/citations/sources/{self.source_incomplete.id}/citation/',
            {'format': 'apa7'}
        )

        # Should return 202 Accepted
        self.assertEqual(response.status_code, 202)
        self.assertIn('task_id', response.data)
        self.assertIn('status_url', response.data)
        self.assertEqual(response.data['task_id'], task_id)
        self.assertEqual(response.data['status_url'], f'/api/v1/citations/tasks/{task_id}/')

        # Verify task was queued
        mock_task_delay.assert_called_once_with(self.source_incomplete.id, 'apa7')

    @patch('apps.citations.views.generate_structured_citation')
    def test_complete_metadata_returns_200_synchronously(self, mock_structured_citation):
        """Test endpoint returns 200 OK for complete metadata (structured citation)"""
        # Mock structured citation service
        mock_structured_citation.return_value = 'Smith, J., & Doe, J. (2024). Complete Article. Test Journal, 42(3), 123-145.'

        response = self.client.post(
            f'/api/v1/citations/sources/{self.source_complete.id}/citation/',
            {'format': 'apa7'}
        )

        # Should return 200 OK synchronously
        self.assertEqual(response.status_code, 200)
        self.assertIn('citation', response.data)
        self.assertIn('citation_html', response.data)
        self.assertEqual(response.data['format'], 'apa7')
        self.assertEqual(response.data['source'], 'structured')
        self.assertFalse(response.data['cached'])

    @patch('apps.citations.views.AsyncResult')
    def test_task_status_pending(self, mock_async_result):
        """Test task status endpoint for pending task"""
        # Mock pending task
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task

        # Use a UUID-like task ID (Celery task IDs are UUIDs)
        response = self.client.get('/api/v1/citations/tasks/12345678-1234-1234-1234-123456789abc/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'pending')
        self.assertNotIn('result', response.data)

    @patch('apps.citations.views.AsyncResult')
    def test_task_status_completed(self, mock_async_result):
        """Test task status endpoint for completed task"""
        # Mock completed task
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {
            'source_id': self.source_incomplete.id,
            'format': 'apa7',
            'citation': 'Test, A. (2024). Test Article.',
            'citation_html': 'Test, A. (2024). <i>Test Article</i>.',
            'cached': False
        }
        mock_async_result.return_value = mock_task

        response = self.client.get('/api/v1/citations/tasks/12345678-1234-1234-1234-123456789abc/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('result', response.data)
        self.assertEqual(response.data['result']['citation'], 'Test, A. (2024). Test Article.')

    @patch('apps.citations.views.AsyncResult')
    def test_task_status_failed(self, mock_async_result):
        """Test task status endpoint for failed task"""
        # Mock failed task
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = Exception("API error")
        mock_async_result.return_value = mock_task

        response = self.client.get('/api/v1/citations/tasks/12345678-1234-1234-1234-123456789abc/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIn('error', response.data)


class RateLimitingTests(TestCase):
    """Tests for AI citation rate limiting"""

    def setUp(self):
        """Set up test data"""
        from django.contrib.auth import get_user_model
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from django.core.cache import cache
        from rest_framework.test import APIClient

        User = get_user_model()

        # Use DRF APIClient instead of Django Client
        self.client = APIClient()

        # Clear cache before each test
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create test vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault description',
            owner=self.user
        )

        # Create test source with incomplete metadata (triggers AI citation)
        self.source = Source.objects.create(
            title='Test Article',
            url='https://example.com/article',
            vault=self.vault,
            created_by=self.user,
            metadata={'abstract': 'Test abstract'}  # Missing required fields for structured citation
        )

    def test_increment_ai_citation_counter(self):
        """Test incrementing AI citation counters"""
        from apps.citations.rate_limiting import increment_ai_citation_counter
        from django.core.cache import cache
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"ai_citation:user:{self.user.id}:daily:{today}"
        vault_key = f"ai_citation:vault:{self.vault.id}:daily:{today}"

        # Initial state
        self.assertEqual(cache.get(user_key, 0), 0)
        self.assertEqual(cache.get(vault_key, 0), 0)

        # Increment once
        increment_ai_citation_counter(self.user.id, self.vault.id)

        self.assertEqual(cache.get(user_key), 1)
        self.assertEqual(cache.get(vault_key), 1)

        # Increment again
        increment_ai_citation_counter(self.user.id, self.vault.id)

        self.assertEqual(cache.get(user_key), 2)
        self.assertEqual(cache.get(vault_key), 2)

    def test_check_ai_citation_rate_limit_allowed(self):
        """Test rate limit check when within limits"""
        from apps.citations.rate_limiting import check_ai_citation_rate_limit

        is_allowed, error_message = check_ai_citation_rate_limit(self.user, self.vault)

        self.assertTrue(is_allowed)
        self.assertIsNone(error_message)

    def test_check_ai_citation_rate_limit_user_exceeded(self):
        """Test rate limit check when user limit exceeded"""
        from apps.citations.rate_limiting import (
            check_ai_citation_rate_limit,
            USER_DAILY_LIMIT,
        )
        from django.core.cache import cache
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"ai_citation:user:{self.user.id}:daily:{today}"

        # Set user count to limit
        cache.set(user_key, USER_DAILY_LIMIT, timeout=86400)

        is_allowed, error_message = check_ai_citation_rate_limit(self.user, self.vault)

        self.assertFalse(is_allowed)
        self.assertIsNotNone(error_message)
        self.assertIn('user', error_message)
        self.assertIn(str(USER_DAILY_LIMIT), error_message)

    def test_check_ai_citation_rate_limit_vault_exceeded(self):
        """Test rate limit check when vault limit exceeded"""
        from apps.citations.rate_limiting import (
            check_ai_citation_rate_limit,
            VAULT_DAILY_LIMIT,
        )
        from django.core.cache import cache
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        vault_key = f"ai_citation:vault:{self.vault.id}:daily:{today}"

        # Set vault count to limit
        cache.set(vault_key, VAULT_DAILY_LIMIT, timeout=86400)

        is_allowed, error_message = check_ai_citation_rate_limit(self.user, self.vault)

        self.assertFalse(is_allowed)
        self.assertIsNotNone(error_message)
        self.assertIn('vault', error_message)
        self.assertIn(str(VAULT_DAILY_LIMIT), error_message)

    def test_get_ai_citation_quota(self):
        """Test getting AI citation quota information"""
        from apps.citations.rate_limiting import (
            get_ai_citation_quota,
            increment_ai_citation_counter,
            USER_DAILY_LIMIT,
            VAULT_DAILY_LIMIT,
        )

        # Initial quota
        quota = get_ai_citation_quota(self.user, self.vault)

        self.assertEqual(quota['user_used'], 0)
        self.assertEqual(quota['user_limit'], USER_DAILY_LIMIT)
        self.assertEqual(quota['user_remaining'], USER_DAILY_LIMIT)
        self.assertEqual(quota['vault_used'], 0)
        self.assertEqual(quota['vault_limit'], VAULT_DAILY_LIMIT)
        self.assertEqual(quota['vault_remaining'], VAULT_DAILY_LIMIT)
        self.assertIn('reset_at', quota)

        # Increment and check again
        increment_ai_citation_counter(self.user.id, self.vault.id)
        increment_ai_citation_counter(self.user.id, self.vault.id)

        quota = get_ai_citation_quota(self.user, self.vault)

        self.assertEqual(quota['user_used'], 2)
        self.assertEqual(quota['user_remaining'], USER_DAILY_LIMIT - 2)
        self.assertEqual(quota['vault_used'], 2)
        self.assertEqual(quota['vault_remaining'], VAULT_DAILY_LIMIT - 2)

    @patch('apps.citations.tasks.generate_ai_citation_task.delay')
    def test_rate_limit_endpoint_returns_429(self, mock_task):
        """Test endpoint returns 429 when rate limit exceeded"""
        from apps.citations.rate_limiting import USER_DAILY_LIMIT
        from django.core.cache import cache
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"ai_citation:user:{self.user.id}:daily:{today}"

        # Set user count to limit
        cache.set(user_key, USER_DAILY_LIMIT, timeout=86400)

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Try to generate AI citation
        response = self.client.post(
            f'/api/v1/citations/sources/{self.source.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertIn('quota', response.data)
        self.assertIn('Retry-After', response)

    @patch('apps.citations.tasks.generate_ai_citation_task.delay')
    def test_rate_limit_endpoint_quota_info(self, mock_task):
        """Test 429 response includes quota information"""
        from apps.citations.rate_limiting import USER_DAILY_LIMIT
        from django.core.cache import cache
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"ai_citation:user:{self.user.id}:daily:{today}"

        # Set user count to limit
        cache.set(user_key, USER_DAILY_LIMIT, timeout=86400)

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Try to generate AI citation
        response = self.client.post(
            f'/api/v1/citations/sources/{self.source.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 429)

        # Check quota information in response
        quota = response.data['quota']
        self.assertEqual(quota['user_used'], USER_DAILY_LIMIT)
        self.assertEqual(quota['user_limit'], USER_DAILY_LIMIT)
        self.assertEqual(quota['user_remaining'], 0)
        self.assertIn('reset_at', quota)

    @patch('apps.citations.services.ai_citation.generate_ai_citation')
    @patch('apps.citations.tasks.generate_ai_citation_task.delay')
    def test_rate_limit_allows_within_limit(self, mock_task, mock_ai_citation):
        """Test endpoint allows AI citation generation when within limits"""
        from django.core.cache import cache

        # Clear cache
        cache.clear()

        # Mock task ID
        mock_task.return_value.id = '12345678-1234-1234-1234-123456789abc'

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Generate AI citation (should succeed)
        response = self.client.post(
            f'/api/v1/citations/sources/{self.source.id}/citation/',
            {'format': 'apa7'},
            format='json'
        )

        self.assertEqual(response.status_code, 202)
        self.assertIn('task_id', response.data)
        self.assertIn('status_url', response.data)

        # Verify counter was incremented
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"ai_citation:user:{self.user.id}:daily:{today}"
        vault_key = f"ai_citation:vault:{self.vault.id}:daily:{today}"

        self.assertEqual(cache.get(user_key), 1)
        self.assertEqual(cache.get(vault_key), 1)


class BatchExportTests(TestCase):
    """Tests for batch citation export endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        from apps.users.models import User
        from apps.vaults.models import Vault, VaultMembership, RoleChoices
        from apps.sources.models import Source

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for batch export',
            owner=self.user
        )

        # Create sources with complete metadata (for structured citations)
        self.source1 = Source.objects.create(
            vault=self.vault,
            title='First Article',
            url='https://example.com/article1',
            created_by=self.user,
            metadata={
                'authors': ['Smith, John', 'Doe, Jane'],
                'publication_date': '2023-05-15',
                'journal': 'Journal of Examples',
                'volume': '42',
                'issue': '3',
                'pages': '123-145'
            }
        )

        self.source2 = Source.objects.create(
            vault=self.vault,
            title='Second Article',
            url='https://example.com/article2',
            created_by=self.user,
            metadata={
                'authors': ['Johnson, Mary'],
                'publication_date': '2024-01-10',
                'journal': 'Another Journal',
                'volume': '10',
                'pages': '50-75'
            }
        )

        # Create REST API client
        from rest_framework.test import APIClient
        self.client = APIClient()

    def test_export_citations_bibtex(self):
        """Test exporting citations in BibTeX format"""
        # Authenticate
        self.client.force_authenticate(user=self.user)

        # First verify vault access works
        vault_detail_url = f'/api/v1/vaults/{self.vault.id}/'
        vault_response = self.client.get(vault_detail_url)
        print(f'\nVault detail URL: {vault_detail_url}')
        print(f'Vault detail status: {vault_response.status_code}')
        if vault_response.status_code != 200:
            print(f'Vault detail error: {vault_response.data if hasattr(vault_response, "data") else vault_response.content}')

        # Export citations
        url = f'/api/v1/citations/vaults/{self.vault.id}/export/'
        print(f'Testing URL: {url}')
        print(f'Vault ID type: {type(self.vault.id)}')
        print(f'Vault ID value: {self.vault.id}')
        response = self.client.get(url, {'format': 'bibtex'})

        print(f'Response status: {response.status_code}')
        if response.status_code != 200:
            print(f'Response data: {response.data if hasattr(response, "data") else response.content}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/x-bibtex')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.bib', response['Content-Disposition'])

        # Check content contains BibTeX entries
        content = response.content.decode('utf-8')
        self.assertIn('@article{', content)
        self.assertIn('author = {', content)
        self.assertIn('title = {', content)

    def test_export_citations_apa7(self):
        """Test exporting citations in APA 7th format"""
        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'apa7'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.txt', response['Content-Disposition'])

        # Check content is not empty
        content = response.content.decode('utf-8')
        self.assertGreater(len(content), 0)

    def test_export_citations_cached(self):
        """Test exporting citations uses cache when available"""
        # Pre-cache citations for both sources
        self.source1.metadata['citations'] = {
            'apa7': {
                'text': 'Cached citation for source 1',
                'html': 'Cached citation for source 1',
                'generated_at': '2024-01-01T00:00:00',
                'source': 'structured'
            }
        }
        self.source1.save()

        self.source2.metadata['citations'] = {
            'apa7': {
                'text': 'Cached citation for source 2',
                'html': 'Cached citation for source 2',
                'generated_at': '2024-01-01T00:00:00',
                'source': 'structured'
            }
        }
        self.source2.save()

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'apa7'}
        )

        self.assertEqual(response.status_code, 200)

        # Check content uses cached citations
        content = response.content.decode('utf-8')
        self.assertIn('Cached citation for source 1', content)
        self.assertIn('Cached citation for source 2', content)

    def test_export_citations_missing_format(self):
        """Test export fails when format parameter is missing"""
        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Export without format
        response = self.client.get(
            f'/api/v1/vaults/{self.vault.id}/citations/'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('format', response.data)

    def test_export_citations_invalid_format(self):
        """Test export fails with invalid format"""
        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Export with invalid format
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'invalid'}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('format', response.data)

    def test_export_citations_empty_vault(self):
        """Test export fails when vault has no sources"""
        from apps.vaults.models import Vault

        # Create empty vault
        empty_vault = Vault.objects.create(
            name='Empty Vault',
            description='Vault with no sources',
            owner=self.user
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Export from empty vault
        response = self.client.get(
            f'/api/v1/vaults/{empty_vault.id}/citations/export/',
            {'format': 'apa7'}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_export_citations_no_permission(self):
        """Test export fails when user has no vault permission"""
        from apps.users.models import User

        # Create another user without vault access
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )

        # Authenticate as other user
        self.client.force_authenticate(user=other_user)

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'apa7'}
        )

        self.assertEqual(response.status_code, 403)

    def test_export_citations_viewer_role(self):
        """Test export works for users with viewer role"""
        from apps.users.models import User
        from apps.vaults.models import VaultMembership, RoleChoices

        # Create another user
        viewer_user = User.objects.create_user(
            email='viewer@example.com',
            username='vieweruser',
            password='testpass123'
        )

        # Add viewer membership
        VaultMembership.objects.create(
            vault=self.vault,
            user=viewer_user,
            role=RoleChoices.VIEWER
        )

        # Authenticate as viewer
        self.client.force_authenticate(user=viewer_user)

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'bibtex'}
        )

        self.assertEqual(response.status_code, 200)


class ProgressiveExportTests(TestCase):
    """Tests for progressive batch export strategy (US-012)"""

    def setUp(self):
        """Set up test data"""
        from apps.users.models import User
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from rest_framework.test import APIClient

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for progressive export',
            owner=self.user
        )

        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_small_vault_sync_export(self):
        """Test small vault (≤50 sources) returns synchronous file download"""
        from apps.sources.models import Source

        # Create 50 sources (small vault)
        for i in range(50):
            Source.objects.create(
                vault=self.vault,
                title=f'Source {i}',
                url=f'https://example.com/{i}',
                created_by=self.user,
                metadata={'authors': ['Author'], 'publication_date': '2024'}
            )

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'apa7'}
        )

        # Should return 200 OK with file download
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_medium_vault_sync_export(self):
        """Test medium vault (51-200 sources) returns synchronous file download"""
        from apps.sources.models import Source

        # Create 100 sources (medium vault)
        for i in range(100):
            Source.objects.create(
                vault=self.vault,
                title=f'Source {i}',
                url=f'https://example.com/{i}',
                created_by=self.user,
                metadata={'authors': ['Author'], 'publication_date': '2024'}
            )

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'mla9'}
        )

        # Should return 200 OK with file download
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('attachment', response['Content-Disposition'])

    @patch('apps.citations.export_views.export_vault_citations_task')
    def test_large_vault_async_export(self, mock_task):
        """Test large vault (>200 sources) returns 202 Accepted with task_id"""
        from apps.sources.models import Source

        # Mock task delay to return task result
        mock_result = MagicMock()
        mock_result.id = 'test-task-id-123'
        mock_task.delay.return_value = mock_result

        # Create 250 sources (large vault)
        for i in range(250):
            Source.objects.create(
                vault=self.vault,
                title=f'Source {i}',
                url=f'https://example.com/{i}',
                created_by=self.user,
                metadata={'authors': ['Author'], 'publication_date': '2024'}
            )

        # Export citations
        response = self.client.get(
            f'/api/v1/citations/vaults/{self.vault.id}/export/',
            {'format': 'bibtex'}
        )

        # Should return 202 Accepted with task info
        self.assertEqual(response.status_code, 202)
        self.assertIn('task_id', response.data)
        self.assertIn('status_url', response.data)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['source_count'], 250)

        # Verify task was called
        mock_task.delay.assert_called_once_with(
            str(self.vault.id),
            'bibtex',
            self.user.id
        )

    @patch('apps.citations.export_views.AsyncResult')
    def test_export_status_pending(self, mock_async_result):
        """Test export status endpoint returns pending status"""
        # Mock AsyncResult to return pending state
        mock_result = MagicMock()
        mock_result.state = 'PENDING'
        mock_async_result.return_value = mock_result

        # Check status
        response = self.client.get('/api/v1/citations/export/status/test-task-123/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIsNone(response.data['progress'])

    @patch('apps.citations.export_views.AsyncResult')
    def test_export_status_completed(self, mock_async_result):
        """Test export status endpoint returns completed status with download URL"""
        # Mock AsyncResult to return success state
        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.result = {
            'vault_id': str(self.vault.id),
            'format': 'apa7',
            'cache_key': 'export_file:vault-id:apa7:user-id',
            'citation_count': 250,
            'expires_at': '2024-01-16T10:30:00Z',
        }
        mock_async_result.return_value = mock_result

        # Check status
        response = self.client.get('/api/v1/citations/export/status/test-task-123/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('download_url', response.data)
        self.assertEqual(response.data['result']['citation_count'], 250)

    @patch('apps.citations.export_views.AsyncResult')
    def test_export_status_failed(self, mock_async_result):
        """Test export status endpoint returns failed status with error"""
        # Mock AsyncResult to return failure state
        mock_result = MagicMock()
        mock_result.state = 'FAILURE'
        mock_result.info = Exception('Export failed')
        mock_async_result.return_value = mock_result

        # Check status
        response = self.client.get('/api/v1/citations/export/status/test-task-123/')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIn('error', response.data)

    @patch('apps.citations.export_views.cache')
    def test_export_download_success(self, mock_cache):
        """Test export download endpoint returns file from cache"""
        # Mock cache to return file data
        mock_cache.get.return_value = {
            'content': '@article{Author2024,\n  author={Author, A.},\n  title={Test Article},\n}',
            'filename': 'Test Vault-citations.bib',
            'content_type': 'application/x-bibtex',
            'expires_at': '2024-01-16T10:30:00Z',
        }

        # Download file
        response = self.client.get('/api/v1/citations/export/download/test-cache-key/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/x-bibtex')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(b'Test Article', response.content)

    @patch('apps.citations.export_views.cache')
    def test_export_download_expired(self, mock_cache):
        """Test export download endpoint returns error when file expired"""
        # Mock cache to return None (expired)
        mock_cache.get.return_value = None

        # Download file
        response = self.client.get('/api/v1/citations/export/download/test-cache-key/')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
