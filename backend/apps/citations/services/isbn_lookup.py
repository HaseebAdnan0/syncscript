"""ISBN metadata lookup service using OpenLibrary API"""
import re
import urllib.request
import urllib.error
import json
from typing import Optional


def normalize_isbn(isbn_input: str) -> Optional[str]:
    """
    Extract and normalize ISBN from various input formats.

    Handles formats:
    - ISBN-10: 0-123-45678-9, 0123456789
    - ISBN-13: 978-0-123-45678-9, 9780123456789
    - With or without hyphens

    Returns:
        Normalized ISBN string (digits only) or None if invalid
    """
    if not isbn_input:
        return None

    # Remove whitespace and hyphens
    isbn_clean = isbn_input.strip().replace('-', '').replace(' ', '')

    # ISBN-13 pattern (13 digits starting with 978 or 979)
    if re.match(r'^(978|979)\d{10}$', isbn_clean):
        return isbn_clean

    # ISBN-10 pattern (10 characters, last can be X)
    if re.match(r'^\d{9}[\dX]$', isbn_clean, re.IGNORECASE):
        return isbn_clean.upper()

    return None


def fetch_isbn_metadata(isbn: str) -> Optional[dict]:
    """
    Fetch metadata from OpenLibrary API for a given ISBN.

    Args:
        isbn: ISBN string in any supported format

    Returns:
        Dictionary with metadata fields or None if fetch fails:
        {
            'title': str,
            'authors': list[str],  # ["Author Name", ...]
            'publication_date': str,  # YYYY or YYYY-MM-DD
            'publisher': str,
            'edition': str,
            'pages': int,
            'isbn_10': str,
            'isbn_13': str,
        }
    """
    # Normalize ISBN
    normalized_isbn = normalize_isbn(isbn)
    if not normalized_isbn:
        return None

    try:
        # OpenLibrary API endpoint
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{normalized_isbn}&format=json&jscmd=data"

        # Make request with timeout
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Check if we got results
        key = f"ISBN:{normalized_isbn}"
        if key not in data or not data[key]:
            return None

        book = data[key]

        # Extract metadata
        metadata: dict = {}

        # Title (required)
        if 'title' in book:
            metadata['title'] = book['title']
        else:
            return None  # Title is required

        # Authors
        authors = []
        if 'authors' in book:
            for author in book['authors']:
                if 'name' in author:
                    authors.append(author['name'])
        metadata['authors'] = authors if authors else ['Unknown']

        # Publication date
        pub_date = book.get('publish_date', '')
        # Try to extract year from various formats
        if pub_date:
            # Extract 4-digit year
            year_match = re.search(r'\d{4}', pub_date)
            if year_match:
                metadata['publication_date'] = year_match.group(0)
            else:
                metadata['publication_date'] = pub_date
        else:
            metadata['publication_date'] = 'n.d.'

        # Publisher
        publishers = book.get('publishers', [])
        if publishers:
            metadata['publisher'] = publishers[0].get('name', '') if isinstance(publishers[0], dict) else str(publishers[0])
        else:
            metadata['publisher'] = ''

        # Edition (if available)
        metadata['edition'] = ''
        if 'notes' in book and 'edition' in book['notes'].lower():
            metadata['edition'] = book['notes']

        # Pages
        metadata['pages'] = book.get('number_of_pages', 0)

        # ISBN-10 and ISBN-13
        identifiers = book.get('identifiers', {})
        isbn_10_list = identifiers.get('isbn_10', [])
        isbn_13_list = identifiers.get('isbn_13', [])

        metadata['isbn_10'] = isbn_10_list[0] if isbn_10_list else ''
        metadata['isbn_13'] = isbn_13_list[0] if isbn_13_list else ''

        # If we started with one format, ensure both are populated if available
        if len(normalized_isbn) == 10:
            metadata['isbn_10'] = normalized_isbn
        elif len(normalized_isbn) == 13:
            metadata['isbn_13'] = normalized_isbn

        return metadata

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, Exception):
        # Return None on any API failure, network error, or invalid ISBN
        return None
