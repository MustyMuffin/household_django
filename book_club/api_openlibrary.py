import requests
from urllib.parse import quote

def fetch_openlibrary_data(title):
    query = quote(title)
    url = f"https://openlibrary.org/search.json?title={query}"

    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    if not data.get("docs"):
        return None

    doc = data["docs"][0]
    return {
        "title": doc.get("title"),
        "authors": doc.get("author_name", []),
        "cover_url": f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg" if "cover_i" in doc else None,
        "openlibrary_link": f"https://openlibrary.org{doc['key']}",
    }
