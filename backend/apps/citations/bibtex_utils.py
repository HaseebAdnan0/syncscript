"""
BibTeX utility functions for escaping special characters and generating valid BibTeX keys.

This module provides utilities for handling BibTeX-specific formatting requirements:
- Escaping special characters for LaTeX compilation
- Handling Unicode characters with LaTeX macros
- Generating valid, unique BibTeX citation keys
"""

import re
from typing import Set


def escape_bibtex(text: str) -> str:
    """
    Escape special characters in text for BibTeX/LaTeX compatibility.

    Args:
        text: The text to escape

    Returns:
        Escaped text safe for BibTeX/LaTeX compilation

    Examples:
        >>> escape_bibtex("Price: $50 & 10% off")
        'Price: \\$50 \\& 10\\% off'
        >>> escape_bibtex("Research in {ML}")
        'Research in \\{ML\\}'
    """
    if not text:
        return text

    # Map of special characters to their escaped versions
    replacements = {
        '\\': r'\\',  # Must be first to avoid double-escaping
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\~{}',  # Tilde needs special handling
        '^': r'\^{}',  # Caret needs special handling
    }

    # Apply replacements
    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)

    return result


def escape_unicode(text: str) -> str:
    """
    Convert Unicode characters to LaTeX macros for BibTeX compatibility.

    Handles common diacritics and special characters used in academic citations.

    Args:
        text: Text containing Unicode characters

    Returns:
        Text with Unicode replaced by LaTeX macros

    Examples:
        >>> escape_unicode("café")
        'caf{\\'e}'
        >>> escape_unicode("Müller")
        'M{\\"u}ller'
    """
    if not text:
        return text

    # Common Unicode to LaTeX mappings for academic citations
    unicode_map = {
        # Acute accents
        'á': "{\\'a}", 'é': "{\\'e}", 'í': "{\\'i}", 'ó': "{\\'o}", 'ú': "{\\'u}",
        'Á': "{\\'A}", 'É': "{\\'E}", 'Í': "{\\'I}", 'Ó': "{\\'O}", 'Ú': "{\\'U}",
        'ý': "{\\'y}", 'Ý': "{\\'Y}",

        # Grave accents
        'à': "{\\`a}", 'è': "{\\`e}", 'ì': "{\\`i}", 'ò': "{\\`o}", 'ù': "{\\`u}",
        'À': "{\\`A}", 'È': "{\\`E}", 'Ì': "{\\`I}", 'Ò': "{\\`O}", 'Ù': "{\\`U}",

        # Circumflex
        'â': "{\\^a}", 'ê': "{\\^e}", 'î': "{\\^i}", 'ô': "{\\^o}", 'û': "{\\^u}",
        'Â': "{\\^A}", 'Ê': "{\\^E}", 'Î': "{\\^I}", 'Ô': "{\\^O}", 'Û': "{\\^U}",

        # Umlaut
        'ä': '{\\"a}', 'ë': '{\\"e}', 'ï': '{\\"i}', 'ö': '{\\"o}', 'ü': '{\\"u}',
        'Ä': '{\\"A}', 'Ë': '{\\"E}', 'Ï': '{\\"I}', 'Ö': '{\\"O}', 'Ü': '{\\"U}',
        'ÿ': '{\\"y}', 'Ÿ': '{\\"Y}',

        # Tilde
        'ñ': '{\\~n}', 'Ñ': '{\\~N}',
        'ã': '{\\~a}', 'õ': '{\\~o}',
        'Ã': '{\\~A}', 'Õ': '{\\~O}',

        # Cedilla
        'ç': '{\\c{c}}', 'Ç': '{\\c{C}}',

        # Nordic
        'å': '{\\aa}', 'Å': '{\\AA}',
        'ø': '{\\o}', 'Ø': '{\\O}',
        'æ': '{\\ae}', 'Æ': '{\\AE}',

        # German sharp s
        'ß': '{\\ss}',

        # Other common academic characters
        '\u2013': '--',  # En dash
        '\u2014': '---',  # Em dash
        '\u2018': "`",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': "``",  # Left double quote
        '\u201d': "''",  # Right double quote
        '\u2026': '{\\ldots}',  # Ellipsis
    }

    result = text
    for char, replacement in unicode_map.items():
        result = result.replace(char, replacement)

    return result


def generate_bibtex_key(
    authors: str | list[str] | None,
    year: str | int | None,
    title: str | None,
    used_keys: Set[str] | None = None
) -> str:
    """
    Generate a valid BibTeX citation key in AuthorYear format.

    Handles duplicate keys by appending a/b/c suffixes.

    Args:
        authors: Author name(s) as string or list
        year: Publication year
        title: Publication title (used if no author)
        used_keys: Set of already-used keys to avoid duplicates

    Returns:
        Valid BibTeX key (e.g., "Smith2024", "JonesEtal2024a")

    Examples:
        >>> generate_bibtex_key("Smith, John", 2024, "Article Title")
        'Smith2024'
        >>> generate_bibtex_key(["Smith, J.", "Jones, A."], 2024, "Title")
        'SmithJones2024'
        >>> generate_bibtex_key(None, 2024, "Anonymous Article")
        'Anonymous2024'
    """
    if used_keys is None:
        used_keys = set()

    # Extract year
    year_str = "n.d."
    if year:
        # Extract 4-digit year from various formats
        year_match = re.search(r'\d{4}', str(year))
        if year_match:
            year_str = year_match.group(0)

    # Extract first author's last name
    author_part = "Anonymous"
    if authors:
        # Handle list of authors
        if isinstance(authors, list):
            authors_str = authors[0] if authors else ""
        else:
            authors_str = str(authors)

        # Extract last name from various formats
        # "Last, First" or "First Last"
        if ',' in authors_str:
            # "Last, First" format
            author_part = authors_str.split(',')[0].strip()
        else:
            # "First Last" format - take last word
            parts = authors_str.strip().split()
            if parts:
                author_part = parts[-1]

        # Add "Etal" suffix for multiple authors (if more than 3)
        if isinstance(authors, list) and len(authors) > 3:
            author_part += "Etal"
        elif isinstance(authors, list) and len(authors) > 1:
            # For 2-3 authors, concatenate last names
            second_author = authors[1]
            if ',' in second_author:
                second_last = second_author.split(',')[0].strip()
            else:
                parts = second_author.strip().split()
                second_last = parts[-1] if parts else ""
            if second_last:
                author_part += second_last

    elif title:
        # No author - use first word of title
        title_words = re.findall(r'\w+', title)
        if title_words:
            author_part = title_words[0]

    # Remove special characters from author part
    author_part = re.sub(r'[^a-zA-Z]', '', author_part)

    # Generate base key
    base_key = f"{author_part}{year_str}"

    # Handle duplicates with a/b/c suffixes
    if base_key not in used_keys:
        return base_key

    # Try suffixes a-z
    for suffix in 'abcdefghijklmnopqrstuvwxyz':
        key_with_suffix = f"{base_key}{suffix}"
        if key_with_suffix not in used_keys:
            return key_with_suffix

    # If all suffixes exhausted, append number
    counter = 1
    while True:
        key_with_number = f"{base_key}{counter}"
        if key_with_number not in used_keys:
            return key_with_number
        counter += 1


def format_bibtex_value(value: str, escape_special: bool = True) -> str:
    """
    Format a value for BibTeX field, handling escaping and Unicode.

    Args:
        value: The value to format
        escape_special: Whether to escape special characters (default True)

    Returns:
        Formatted value safe for BibTeX

    Examples:
        >>> format_bibtex_value("Machine Learning & AI: 100% Success")
        'Machine Learning \\& AI: 100\\% Success'
        >>> format_bibtex_value("Café Culture")
        'Caf{\\'e} Culture'
    """
    if not value:
        return ""

    result = value

    # First escape special characters (if enabled), BEFORE Unicode conversion
    # This prevents escaping LaTeX commands created by Unicode conversion
    if escape_special:
        result = escape_bibtex(result)

    # Then handle Unicode characters (creates LaTeX commands with braces)
    result = escape_unicode(result)

    return result
