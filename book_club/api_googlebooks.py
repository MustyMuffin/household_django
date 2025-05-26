import requests
from urllib.parse import quote
from django.conf import settings

def fetch_google_books(title):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    query = quote(title)
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{query}&key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    if not data.get("items"):
        return None

    volume = data["items"][0]["volumeInfo"]
    return {
        "title": volume.get("title"),
        "authors": volume.get("authors", []),
        "description": volume.get("description", ""),
        "thumbnail": volume.get("imageLinks", {}).get("thumbnail"),
        "preview_link": volume.get("previewLink"),
    }
