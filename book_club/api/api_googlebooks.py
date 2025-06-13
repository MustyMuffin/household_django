import requests, json
from urllib.parse import quote
from django.conf import settings
from django.http import JsonResponse


def estimate_words(page_count):
    try:
        return int(page_count) * 250 if page_count else 0
    except (ValueError, TypeError):
        return 0

def fetch_google_books_multiple(query):
    import requests
    response = requests.get("https://www.googleapis.com/books/v1/volumes", params={
        "q": query,
        "maxResults": 5,
    })
    data = response.json()

    results = []
    for item in data.get("items", []):
        volume = item.get("volumeInfo", {})
        results.append({
            "title": volume.get("title"),
            "authors": volume.get("authors", []),
            "description": volume.get("description"),
            "thumbnail": volume.get("imageLinks", {}).get("thumbnail", ""),
            "preview_link": volume.get("previewLink", ""),
            "pageCount": volume.get("pageCount"),
            "volume_id": item.get("id"),  # 🆕 Add this for linking to details
        })
    return results


def fetch_google_books_volume(volume_id):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return {}

    info = response.json().get("volumeInfo", {})

    return {
        "title": info.get("title"),
        "authors": info.get("authors", []),
        "description": info.get("description"),
        "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
        "preview_link": info.get("previewLink", ""),
        "pageCount": info.get("pageCount"),
        "estimated_words": estimate_words(info.get("pageCount")),
    }

def fetch_google_volume_detail(request, volume_id):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}?key={api_key}"
    print("DEBUG url", url)

    response = requests.get(url)
    if response.status_code != 200:
        return JsonResponse({"success": False, "error": "Not found"}, status=404)

    data = response.json()
    info = data.get("volumeInfo", {})

    return JsonResponse({
        "success": True,
        "title": info.get("title"),
        "authors": info.get("authors", []),
        "description": info.get("description", ""),
        "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
        "pageCount": info.get("pageCount"),
    })