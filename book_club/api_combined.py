from .api_googlebooks import fetch_google_books
from .api_openlibrary import fetch_openlibrary_data
from .models import BookMetadata

def fetch_and_cache_metadata(book):
    # Check for existing metadata
    if hasattr(book, 'metadata'):
        return book.metadata

    # Try Google Books
    data = fetch_google_books(book.text)
    if data:
        metadata = BookMetadata.objects.create(
            book=book,
            source="google",
            title=data.get("title"),
            authors=data.get("authors", []),
            description=data.get("description", ""),
            thumbnail_url=data.get("thumbnail", ""),
            external_url=data.get("preview_link", "")
        )
        return metadata

    # Fallback to Open Library
    data = fetch_openlibrary_data(book.text)
    if data:
        metadata = BookMetadata.objects.create(
            book=book,
            source="openlibrary",
            title=data.get("title"),
            authors=data.get("authors", []),
            thumbnail_url=data.get("cover_url", ""),
            external_url=data.get("openlibrary_link", "")
        )
        return metadata

    return None

