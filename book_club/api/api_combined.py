from book_club.api.api_googlebooks import fetch_google_books_multiple
from book_club.api.api_openlibrary import fetch_openlibrary_results


def fetch_all_metadata_options(title):
    google = fetch_google_books_multiple(title) or []
    openlib = fetch_openlibrary_results(title) or []

    return {
        "google": google,
        "openlibrary": openlib
    }

def fetch_and_cache_metadata(book):
    """Return a list of metadata options for a book."""
    candidates = []

    google_results = fetch_google_books_multiple(book.title)
    for item in google_results:
        candidates.append({
            'source': 'google',
            'title': item.get('title'),
            'authors': item.get('authors', []),
            'description': item.get('description', ''),
            'thumbnail_url': item.get('thumbnail', ''),
            'external_url': item.get('preview_link', ''),
            'pages': item.get('pageCount'),
            'volume_id': item.get('volume_id'),
        })

    ol_result = fetch_openlibrary_results(book.title)
    if ol_result:
        candidates.append({
            'source': 'openlibrary',
            'title': ol_result.get('title'),
            'authors': ol_result.get('authors', []),
            'description': '',
            'thumbnail_url': ol_result.get('cover_url', ''),
            'external_url': ol_result.get('openlibrary_link', ''),
            'pages': ol_result.get('pageCount'),
        })

    return candidates

