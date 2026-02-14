"""DOI metadata lookup service using CrossRef API"""
import re
from typing import Optional
from crossref_commons.retrieval import get_publication_as_json


def normalize_doi(doi_input: str) -> Optional[str]:
    """
    Extract and normalize DOI from various input formats.

    Handles formats:
    - 10.xxxx/yyyy
    - doi.org/10.xxxx/yyyy
    - https://doi.org/10.xxxx/yyyy
    - http://dx.doi.org/10.xxxx/yyyy

    Returns:
        Normalized DOI string (e.g., "10.1234/example") or None if invalid
    """
    if not doi_input:
        return None

    # Remove whitespace
    doi_input = doi_input.strip()

    # Pattern to match DOI: starts with 10. followed by digits, then /, then anything
    doi_pattern = r'(10\.\d{4,}(?:\.\d+)*\/[^\s]+)'

    match = re.search(doi_pattern, doi_input)
    if match:
        return match.group(1)

    return None


def fetch_doi_metadata(doi: str) -> Optional[dict]:
    """
    Fetch metadata from CrossRef API for a given DOI.

    Args:
        doi: DOI string in any supported format

    Returns:
        Dictionary with metadata fields or None if fetch fails:
        {
            'title': str,
            'authors': list[str],  # ["Last, First", ...]
            'publication_date': str,  # ISO format YYYY-MM-DD
            'journal': str,
            'volume': str,
            'issue': str,
            'pages': str,
            'publisher': str,
            'doi': str,  # normalized DOI
        }
    """
    # Normalize DOI
    normalized_doi = normalize_doi(doi)
    if not normalized_doi:
        return None

    try:
        result = get_publication_as_json(normalized_doi)

        if not result:
            return None

        # Extract metadata
        metadata: dict = {
            'doi': normalized_doi,
        }

        # Title (required)
        if 'title' in result and result['title']:
            metadata['title'] = result['title'][0]
        else:
            return None  # Title is required

        # Authors
        authors = []
        if 'author' in result:
            for author in result['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    # Format: "Last, First"
                    author_str = f"{family}, {given}" if given else family
                    authors.append(author_str)
        metadata['authors'] = authors if authors else ['Unknown']

        # Publication date
        pub_date = None
        if 'published' in result:
            date_parts = result['published'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                year = parts[0] if len(parts) > 0 else None
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                if year:
                    pub_date = f"{year:04d}-{month:02d}-{day:02d}"

        if not pub_date and 'created' in result:
            date_parts = result['created'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                year = parts[0] if len(parts) > 0 else None
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                if year:
                    pub_date = f"{year:04d}-{month:02d}-{day:02d}"

        metadata['publication_date'] = pub_date or 'n.d.'

        # Journal/container title
        if 'container-title' in result and result['container-title']:
            metadata['journal'] = result['container-title'][0]
        else:
            metadata['journal'] = ''

        # Volume
        metadata['volume'] = result.get('volume', '')

        # Issue
        metadata['issue'] = result.get('issue', '')

        # Pages
        metadata['pages'] = result.get('page', '')

        # Publisher
        metadata['publisher'] = result.get('publisher', '')

        return metadata

    except Exception:
        # Return None on any API failure, network error, or invalid DOI
        return None
