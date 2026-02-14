"""
Structured citation generation service using citeproc-py.

This service generates properly formatted citations for sources with complete metadata
using the Citation Style Language (CSL) processor.
"""

import os
from typing import Dict, Any, Optional
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from citeproc.source.json import CiteProcJSON
from citeproc_styles import get_style_filepath

from apps.citations.models import CitationFormat


def has_complete_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Check if metadata has the minimum required fields for structured citation generation.

    Required fields:
    - title: Must be present and non-empty
    - author(s): At least one author
    - date: Publication date (year at minimum)

    Args:
        metadata: Source metadata dictionary

    Returns:
        True if metadata is complete enough for structured citation, False otherwise
    """
    # Check title
    if not metadata.get('title') or not str(metadata['title']).strip():
        return False

    # Check authors (can be 'author', 'authors', or empty list)
    authors = metadata.get('authors') or metadata.get('author') or []
    if not authors:
        return False

    # If authors is a single string, convert to list
    if isinstance(authors, str):
        authors = [authors]

    # Must have at least one non-empty author
    if not any(str(author).strip() for author in authors):
        return False

    # Check date (can be 'date', 'publication_date', or 'year')
    date = metadata.get('publication_date') or metadata.get('date') or metadata.get('year')
    if not date:
        return False

    return True


def _convert_to_csl_json(metadata: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    """
    Convert source metadata to CSL JSON format.

    CSL JSON spec: https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html

    Args:
        metadata: Source metadata dictionary
        source_id: Unique ID for the source (used as citation key)

    Returns:
        CSL JSON formatted dictionary
    """
    csl_item: Dict[str, Any] = {
        'id': source_id,
        'type': 'article-journal',  # Default type, can be overridden
    }

    # Title
    if metadata.get('title'):
        csl_item['title'] = str(metadata['title'])

    # Authors
    authors = metadata.get('authors') or metadata.get('author') or []
    if isinstance(authors, str):
        authors = [authors]

    csl_authors = []
    for author in authors:
        if isinstance(author, str):
            # Parse "Last, First" or "First Last" format
            if ',' in author:
                parts = author.split(',', 1)
                csl_authors.append({
                    'family': parts[0].strip(),
                    'given': parts[1].strip() if len(parts) > 1 else ''
                })
            else:
                # Simple format: assume last word is family name
                parts = author.strip().split()
                if len(parts) == 1:
                    csl_authors.append({'family': parts[0]})
                else:
                    csl_authors.append({
                        'family': parts[-1],
                        'given': ' '.join(parts[:-1])
                    })
        elif isinstance(author, dict):
            # Already in CSL format
            csl_authors.append(author)

    if csl_authors:
        csl_item['author'] = csl_authors

    # Date
    date_str = metadata.get('publication_date') or metadata.get('date') or metadata.get('year')
    if date_str:
        # Extract year from date string
        date_str = str(date_str)
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = year_match.group(0)
            csl_item['issued'] = {'date-parts': [[int(year)]]}

    # Journal/Publication
    if metadata.get('journal'):
        csl_item['container-title'] = str(metadata['journal'])

    # Volume
    if metadata.get('volume'):
        csl_item['volume'] = str(metadata['volume'])

    # Issue
    if metadata.get('issue'):
        csl_item['issue'] = str(metadata['issue'])

    # Pages
    if metadata.get('pages'):
        csl_item['page'] = str(metadata['pages'])

    # DOI
    if metadata.get('doi'):
        csl_item['DOI'] = str(metadata['doi'])

    # ISBN
    if metadata.get('isbn') or metadata.get('isbn_13') or metadata.get('isbn_10'):
        isbn = metadata.get('isbn') or metadata.get('isbn_13') or metadata.get('isbn_10')
        csl_item['ISBN'] = str(isbn)
        csl_item['type'] = 'book'  # Override type for books

    # Publisher
    if metadata.get('publisher'):
        csl_item['publisher'] = str(metadata['publisher'])
        if 'type' not in csl_item or csl_item['type'] == 'article-journal':
            csl_item['type'] = 'book'  # If has publisher but not journal, likely a book

    # Edition
    if metadata.get('edition'):
        csl_item['edition'] = str(metadata['edition'])

    # URL (for web sources)
    if metadata.get('url'):
        csl_item['URL'] = str(metadata['url'])
        if csl_item['type'] == 'article-journal' and not metadata.get('journal'):
            csl_item['type'] = 'webpage'

    # Access date (for web sources)
    if metadata.get('access_date'):
        csl_item['accessed'] = {'raw': str(metadata['access_date'])}

    return csl_item


def _get_style_file(format: CitationFormat) -> str:
    """
    Get the CSL style file path for a given citation format.

    Args:
        format: Citation format enum value

    Returns:
        Path to CSL style file

    Raises:
        FileNotFoundError: If style file doesn't exist
    """
    # Map our formats to CSL style names
    style_map = {
        CitationFormat.APA7: 'apa-7th-edition',
        CitationFormat.MLA9: 'modern-language-association-9th-edition',
        CitationFormat.CHICAGO17: 'chicago-author-date',
        CitationFormat.IEEE: 'ieee',
        CitationFormat.HARVARD: 'harvard-cite-them-right',
    }

    style_name = style_map.get(format)
    if not style_name:
        raise ValueError(f"Unsupported citation format: {format}")

    # Try to get style from citeproc-styles package
    try:
        style_path = get_style_filepath(style_name)
        if os.path.exists(style_path):
            return style_path
    except Exception:
        pass

    # Fallback: look in our local styles directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    styles_dir = os.path.join(base_dir, 'styles')
    style_path = os.path.join(styles_dir, f'{style_name}.csl')

    if not os.path.exists(style_path):
        raise FileNotFoundError(
            f"CSL style file not found: {style_name}.csl. "
            f"Checked: {style_path}"
        )

    return style_path


def generate_structured_citation(
    metadata: Dict[str, Any],
    format: CitationFormat,
    source_id: str = 'source1'
) -> str:
    """
    Generate a formatted citation using citeproc-py for sources with complete metadata.

    This function uses the Citation Style Language (CSL) processor to generate
    properly formatted citations in various academic styles.

    Args:
        metadata: Source metadata dictionary (must have title, author(s), date at minimum)
        format: Citation format enum (APA7, MLA9, CHICAGO17, IEEE, HARVARD)
        source_id: Unique identifier for the source (default: 'source1')

    Returns:
        Formatted citation string

    Raises:
        ValueError: If metadata is incomplete or format is invalid
        FileNotFoundError: If CSL style file is not found
    """
    # Validate metadata completeness
    if not has_complete_metadata(metadata):
        raise ValueError(
            "Incomplete metadata. Required fields: title, author(s), date. "
            f"Provided: {list(metadata.keys())}"
        )

    # BibTeX handled separately (not CSL-based)
    if format == CitationFormat.BIBTEX:
        return _generate_bibtex(metadata, source_id)

    # Convert metadata to CSL JSON
    csl_item = _convert_to_csl_json(metadata, source_id)

    # Load CSL style
    style_path = _get_style_file(format)

    # Create bibliography
    bib_source = CiteProcJSON([csl_item])
    bib_style = CitationStylesStyle(style_path, validate=False)
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter=None)  # type: ignore[arg-type]

    # Register citation
    citation = Citation([CitationItem(source_id)])
    bibliography.register(citation)

    # Generate bibliography
    for item in bibliography.bibliography():
        # Return the first (and only) citation
        return str(item)

    # Fallback (should never reach here)
    return ""


def _generate_bibtex(metadata: Dict[str, Any], source_id: str) -> str:
    """
    Generate BibTeX citation format.

    BibTeX is not CSL-based, so we generate it manually.

    Args:
        metadata: Source metadata dictionary
        source_id: BibTeX citation key

    Returns:
        BibTeX formatted citation string
    """
    # Determine entry type
    entry_type = 'article'
    if metadata.get('isbn') or metadata.get('publisher'):
        entry_type = 'book'
    elif metadata.get('url') and not metadata.get('journal'):
        entry_type = 'misc'

    # Start BibTeX entry
    lines = [f"@{entry_type}{{{source_id},"]

    # Title
    if metadata.get('title'):
        lines.append(f"  title = {{{metadata['title']}}},")

    # Authors
    authors = metadata.get('authors') or metadata.get('author') or []
    if isinstance(authors, str):
        authors = [authors]
    if authors:
        author_str = ' and '.join(str(a) for a in authors)
        lines.append(f"  author = {{{author_str}}},")

    # Year
    date_str = metadata.get('publication_date') or metadata.get('date') or metadata.get('year')
    if date_str:
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            lines.append(f"  year = {{{year_match.group(0)}}},")

    # Journal/Book-specific fields
    if entry_type == 'article':
        if metadata.get('journal'):
            lines.append(f"  journal = {{{metadata['journal']}}},")
        if metadata.get('volume'):
            lines.append(f"  volume = {{{metadata['volume']}}},")
        if metadata.get('issue'):
            lines.append(f"  number = {{{metadata['issue']}}},")
        if metadata.get('pages'):
            lines.append(f"  pages = {{{metadata['pages']}}},")
    elif entry_type == 'book':
        if metadata.get('publisher'):
            lines.append(f"  publisher = {{{metadata['publisher']}}},")
        if metadata.get('edition'):
            lines.append(f"  edition = {{{metadata['edition']}}},")
        if metadata.get('isbn'):
            lines.append(f"  isbn = {{{metadata['isbn']}}},")

    # DOI
    if metadata.get('doi'):
        lines.append(f"  doi = {{{metadata['doi']}}},")

    # URL
    if metadata.get('url'):
        lines.append(f"  url = {{{metadata['url']}}},")

    # Close entry (remove trailing comma from last field)
    if lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]
    lines.append("}")

    return '\n'.join(lines)
