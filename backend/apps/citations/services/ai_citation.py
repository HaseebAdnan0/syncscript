"""
AI-powered citation generation using Claude.

This service uses Anthropic's Claude API to generate citations for sources
with incomplete metadata, ensuring academic accuracy and proper formatting.
"""

import os
from typing import Dict, Any, Tuple
from datetime import datetime
from anthropic import Anthropic

from apps.citations.models import CitationFormat


def generate_ai_citation(source_data: Dict[str, Any], format: CitationFormat) -> Tuple[str, str]:
    """
    Generate a citation using Claude AI for sources with incomplete metadata.

    This function uses Claude to generate academically accurate citations even when
    metadata is incomplete. It handles missing fields gracefully (e.g., author="Unknown",
    date="n.d.") and includes access dates for web sources.

    Args:
        source_data: Dictionary containing source metadata (title, url, authors, etc.)
        format: Citation format (APA7, MLA9, CHICAGO17, BIBTEX, IEEE, HARVARD)

    Returns:
        Tuple of (plain_text_citation, html_citation)
        - plain_text: Citation with no formatting
        - html: Citation with HTML tags for italicization (journal names, titles)

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not configured
        Exception: If Claude API call fails
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Build system prompt with format-specific rules
    system_prompt = _build_system_prompt(format)

    # Build user prompt with source data
    user_prompt = _build_user_prompt(source_data, format)

    # Call Claude API
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract response
    # Type: ignore because Anthropic SDK ContentBlock typing is complex
    response_text = message.content[0].text  # type: ignore[attr-defined]

    # Parse plain text and HTML versions from response
    plain_text, html = _parse_response(response_text)

    return plain_text, html


def _build_system_prompt(format: CitationFormat) -> str:
    """
    Build format-specific system prompt for Claude.

    Args:
        format: Citation format

    Returns:
        System prompt string with citation rules
    """
    format_rules = {
        CitationFormat.APA7: """You are an expert academic citation generator specializing in APA 7th Edition.

Rules:
- Author format: Last name, First initial. (multiple authors separated by commas, use & before last author)
- Missing author: Use "Unknown" or organization name if available
- Missing date: Use (n.d.) for "no date"
- Journal/book titles: Italicize in HTML version only
- Web sources: Include "Retrieved [date] from [URL]"
- Article titles: Sentence case (only first word and proper nouns capitalized)
- Journal titles: Title case
- Format: Author, A. A. (Year). Title of article. Journal Name, volume(issue), pages. DOI or URL

Examples:
- Journal: Smith, J. D., & Jones, M. K. (2023). Effects of climate change. Nature, 123(4), 567-589. https://doi.org/10.1234/nature.2023
- Book: Brown, A. (2022). Understanding AI. MIT Press.
- Website: Unknown. (n.d.). Citation guidelines. Retrieved February 14, 2026 from https://example.com/citations""",

        CitationFormat.MLA9: """You are an expert academic citation generator specializing in MLA 9th Edition.

Rules:
- Author format: Last name, First name (reverse only first author if multiple)
- Missing author: Start with title
- Missing date: Use "n.d." for no date
- Book/journal titles: Italicize in HTML version only
- Article titles: Use quotation marks
- Web sources: Include access date
- Format: Author. "Article Title." Journal Title, vol. X, no. Y, Year, pp. Z-ZZ. URL. Accessed Day Month Year.

Examples:
- Journal: Smith, John D., and Mary K. Jones. "Effects of Climate Change." Nature, vol. 123, no. 4, 2023, pp. 567-589, https://doi.org/10.1234/nature.2023.
- Book: Brown, Alice. Understanding AI. MIT Press, 2022.
- Website: "Citation Guidelines." Example Site, https://example.com/citations. Accessed 14 Feb. 2026.""",

        CitationFormat.CHICAGO17: """You are an expert academic citation generator specializing in Chicago Manual of Style 17th Edition (Author-Date).

Rules:
- Author format: Last name, First name (all authors listed)
- Missing author: Use "Anonymous" or organization name
- Missing date: Use "n.d." for no date
- Book/journal titles: Italicize in HTML version only
- Article titles: Use quotation marks
- Web sources: Include access date
- Format: Author. Year. "Article Title." Journal Title volume (issue): pages. DOI or URL.

Examples:
- Journal: Smith, John D., and Mary K. Jones. 2023. "Effects of Climate Change." Nature 123 (4): 567-589. https://doi.org/10.1234/nature.2023.
- Book: Brown, Alice. 2022. Understanding AI. Cambridge, MA: MIT Press.
- Website: Anonymous. n.d. "Citation Guidelines." Example Site. Accessed February 14, 2026. https://example.com/citations.""",

        CitationFormat.BIBTEX: """You are an expert BibTeX citation generator.

Rules:
- Entry types: @article, @book, @misc (for websites/other)
- Required fields vary by type
- Escape special characters: & → \\&, % → \\%, $ → \\$, # → \\#, _ → \\_
- Key format: AuthorYearKeyword (e.g., Smith2023Climate)
- No trailing comma on last field
- Italicization not needed (LaTeX handles formatting)

Examples:
@article{Smith2023Climate,
  author = {Smith, John D. and Jones, Mary K.},
  title = {Effects of Climate Change},
  journal = {Nature},
  year = {2023},
  volume = {123},
  number = {4},
  pages = {567--589},
  doi = {10.1234/nature.2023}
}

@book{Brown2022AI,
  author = {Brown, Alice},
  title = {Understanding AI},
  publisher = {MIT Press},
  year = {2022},
  address = {Cambridge, MA}
}

@misc{Unknown2026Citations,
  title = {Citation Guidelines},
  howpublished = {\\url{https://example.com/citations}},
  note = {Accessed: 2026-02-14}
}""",

        CitationFormat.IEEE: """You are an expert academic citation generator specializing in IEEE citation style.

Rules:
- Use [1] numbering in actual references (omit here, just format the citation)
- Author format: First initial. Last name (all authors listed)
- Missing author: Use "Anonymous"
- Article titles: Use quotation marks
- Journal/book titles: Italicize in HTML version only
- Format: F. I. Lastname, "Article title," Journal Title, vol. X, no. Y, pp. Z-ZZ, Month Year. [Online]. Available: URL

Examples:
- Journal: J. D. Smith and M. K. Jones, "Effects of climate change," Nature, vol. 123, no. 4, pp. 567-589, Apr. 2023. doi: 10.1234/nature.2023
- Book: A. Brown, Understanding AI. Cambridge, MA: MIT Press, 2022.
- Website: "Citation guidelines," Example Site. [Online]. Available: https://example.com/citations. Accessed: Feb. 14, 2026.""",

        CitationFormat.HARVARD: """You are an expert academic citation generator specializing in Harvard referencing style.

Rules:
- Author format: Last name, First initial. (multiple authors separated by commas, use 'and' before last author)
- Missing author: Use organization name or "Anon."
- Missing date: Use "no date"
- Book/journal titles: Italicize in HTML version only
- Article titles: Single quotes
- Web sources: Include access date
- Format: Author, F.I., Year. 'Article title', Journal Title, volume(issue), pp. pages. Available at: URL (Accessed: date).

Examples:
- Journal: Smith, J.D. and Jones, M.K., 2023. 'Effects of climate change', Nature, 123(4), pp. 567-589. doi: 10.1234/nature.2023
- Book: Brown, A., 2022. Understanding AI. Cambridge, MA: MIT Press.
- Website: Anon., no date. 'Citation guidelines'. Available at: https://example.com/citations (Accessed: 14 February 2026)."""
    }

    base_rules = format_rules.get(format, format_rules[CitationFormat.APA7])

    return f"""{base_rules}

CRITICAL INSTRUCTIONS:
1. Return TWO versions separated by "---SPLIT---":
   - First version: Plain text with NO HTML tags
   - Second version: HTML with <i> tags for italicized text ONLY (journals, books, etc.)
2. Handle missing fields gracefully (use n.d., Unknown, Anonymous as appropriate)
3. For web sources, include access date: {datetime.now().strftime("%B %d, %Y")}
4. Be precise with punctuation and spacing
5. Follow the format rules EXACTLY as shown in examples"""


def _build_user_prompt(source_data: Dict[str, Any], format: CitationFormat) -> str:
    """
    Build user prompt with source data.

    Args:
        source_data: Source metadata dictionary
        format: Citation format

    Returns:
        User prompt string
    """
    # Extract available fields
    title = source_data.get('title', 'Untitled')
    url = source_data.get('url', '')
    authors = source_data.get('authors') or source_data.get('author') or []

    # Handle authors as string or list
    if isinstance(authors, str):
        authors = [authors]

    # Extract other metadata fields
    metadata = source_data.get('metadata', {})
    journal = metadata.get('journal', '')
    volume = metadata.get('volume', '')
    issue = metadata.get('issue', '')
    pages = metadata.get('pages', '')
    publisher = metadata.get('publisher', '')
    publication_date = metadata.get('publication_date') or metadata.get('date') or metadata.get('year') or ''
    doi = metadata.get('doi', '')
    isbn = metadata.get('isbn', '')

    # Build structured prompt
    prompt = f"""Generate a {format.value} citation for the following source:

Title: {title}
URL: {url}
Authors: {', '.join(authors) if authors else 'Not provided'}
Publication Date: {publication_date if publication_date else 'Not provided'}
Journal: {journal if journal else 'Not provided'}
Volume: {volume if volume else 'Not provided'}
Issue: {issue if issue else 'Not provided'}
Pages: {pages if pages else 'Not provided'}
Publisher: {publisher if publisher else 'Not provided'}
DOI: {doi if doi else 'Not provided'}
ISBN: {isbn if isbn else 'Not provided'}

Return TWO versions separated by "---SPLIT---":
1. Plain text version (no HTML)
2. HTML version (with <i> tags for italics only)"""

    return prompt


def _parse_response(response_text: str) -> Tuple[str, str]:
    """
    Parse Claude response into plain text and HTML versions.

    Args:
        response_text: Raw response from Claude

    Returns:
        Tuple of (plain_text, html)
    """
    # Split response on separator
    if "---SPLIT---" in response_text:
        parts = response_text.split("---SPLIT---")
        plain_text = parts[0].strip()
        html = parts[1].strip() if len(parts) > 1 else parts[0].strip()
    else:
        # Fallback if separator not found
        plain_text = response_text.strip()
        html = response_text.strip()

    return plain_text, html
