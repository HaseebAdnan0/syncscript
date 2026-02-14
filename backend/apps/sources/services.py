# Services for metadata extraction and other utilities
from typing import TypedDict
from newspaper import Article


class MetadataDict(TypedDict, total=False):
    """Type definition for metadata dictionary returned by extract_metadata."""
    title: str
    authors: list[str]
    publication_date: str | None
    abstract: str
    error: str


def extract_metadata(url: str) -> MetadataDict:
    """
    Extract metadata from a URL using newspaper3k.

    Args:
        url: The URL to extract metadata from

    Returns:
        Dictionary containing title, authors, publication_date, abstract.
        On error, returns {'title': url, 'error': error_message}
    """
    try:
        article = Article(url)
        article.download(timeout=10)
        article.parse()

        # Extract first 500 chars of text as abstract
        abstract = article.text[:500] if article.text else ""

        # Format publication date as string if available
        pub_date = None
        if article.publish_date:
            pub_date = article.publish_date.isoformat()

        return {
            'title': article.title or url,
            'authors': article.authors,
            'publication_date': pub_date,
            'abstract': abstract,
        }
    except Exception as e:
        return {
            'title': url,
            'error': str(e),
