"""Tests for citations app"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.citations.services.doi_lookup import normalize_doi, fetch_doi_metadata
from apps.citations.services.isbn_lookup import normalize_isbn, fetch_isbn_metadata
from apps.citations.services.structured_citation import (
    has_complete_metadata,
    generate_structured_citation,
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
