# Services for metadata extraction and other utilities
from typing import TypedDict
from newspaper import Article, Config


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
        config = Config()
        config.request_timeout = 10
        article = Article(url, config=config)
        article.download()
        article.parse()

        # Extract first 500 chars of text as abstract
        abstract = article.text[:500] if article.text else ""

        # Format publication date as string if available
        pub_date: str | None = None
        if article.publish_date:
            # publish_date could be datetime or string, handle both
            pub_date_obj = article.publish_date
            if hasattr(pub_date_obj, 'isoformat'):
                pub_date = pub_date_obj.isoformat()  # type: ignore[union-attr]
            else:
                pub_date = str(pub_date_obj)

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
        }
