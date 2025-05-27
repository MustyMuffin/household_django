from .api_googlebooks import fetch_google_books
from .api_openlibrary import fetch_openlibrary_data
from .models import BookMetadata, Book

def fetch_and_cache_metadata(book):
    """Attach metadata to a real Book instance if not already cached."""
    if hasattr(book, 'metadata'):
        return book.metadata

    # Try Google Books
    data = fetch_google_books(book.text)
    if data:
        return BookMetadata.objects.create(
            book=book,
            source='google',
            title=data.get('title'),
            authors=data.get('authors', []),
            description=data.get('description', ''),
            thumbnail_url=data.get('thumbnail', ''),
            external_url=data.get('preview_link', ''),
            pages=data.get('pageCount', None),
        )

    # Fallback to Open Library
    data = fetch_openlibrary_data(book.text)
    if data:
        return BookMetadata.objects.create(
            book=book,
            source='openlibrary',
            title=data.get('title'),
            authors=data.get('authors', []),
            description='',
            thumbnail_url=data.get('cover_url', ''),
            external_url=data.get('openlibrary_link', ''),
        )

    return None


def fetch_external_metadata_by_title(title):
    """Fetch metadata based on title, without requiring a Book instance."""
    existing_book = Book.objects.filter(text=title).first()
    if existing_book and hasattr(existing_book, 'metadata'):
        return {
            "source": existing_book.metadata.source,
            "title": existing_book.metadata.title,
            "authors": existing_book.metadata.authors,
            "description": existing_book.metadata.description,
            "thumbnail_url": existing_book.metadata.thumbnail_url,
            "external_url": existing_book.metadata.external_url,
        }

    data = fetch_google_books(title)
    if data:
        return {
            "source": "google",
            "title": data.get("title"),
            "authors": data.get("authors", []),
            "description": data.get("description", ""),
            "thumbnail_url": data.get("thumbnail", ""),
            "external_url": data.get("preview_link", ""),
            "pages": data.get("pages"),
        }

    data = fetch_openlibrary_data(title)
    if data:
        return {
            "source": "openlibrary",
            "title": data.get("title"),
            "authors": data.get("authors", []),
            "description": "",
            "thumbnail_url": data.get("cover_url", ""),
            "external_url": data.get("openlibrary_link", ""),
        }

    return None

