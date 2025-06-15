import requests
import requests
from urllib.parse import quote

from django.conf import settings
from django.http import JsonResponse


def fetch_openlibrary_results(query):
    def fetch_pages_from_edition(edition_key):
        if not edition_key:
            return None
        url = f"https://openlibrary.org/books/{edition_key}.json"
        try:
            res = requests.get(url)
            if res.ok:
                return res.json().get("number_of_pages")
        except Exception as e:
            print(f"Failed to fetch page count for {edition_key}: {e}")
        return None

    def fetch_description_from_work(work_key):
        if not work_key:
            return ""
        # Remove /works/ prefix if present
        work_id = work_key.replace('/works/', '')
        url = f"https://openlibrary.org/works/{work_id}.json"
        try:
            res = requests.get(url)
            if res.ok:
                data = res.json()
                # Description can be a string or dict with 'value' key
                description = data.get("description", "")
                if isinstance(description, dict):
                    description = description.get("value", "")
                return description
        except Exception as e:
            print(f"Failed to fetch description for {work_key}: {e}")
        return ""

    response = requests.get("https://openlibrary.org/search.json", params={"title": query})
    data = response.json()
    results = []

    for item in data.get("docs", [])[:5]:
        edition_key = item.get("cover_edition_key") or (item.get("edition_key", [None])[0])
        page_count = fetch_pages_from_edition(edition_key)

        # Get work key and fetch description
        work_key = item.get("key")  # This is usually /works/OLXXXXXX
        description = fetch_description_from_work(work_key)

        results.append({
            "title": item.get("title"),
            "key": item.get("key"),
            "authors": item.get("author_name", []),
            "description": description,  # Now includes actual description
            "thumbnail": f"https://covers.openlibrary.org/b/olid/{edition_key}-M.jpg" if edition_key else "",
            "external_url": f"https://openlibrary.org{item.get('key')}",
            "pageCount": page_count,
        })
        # print(f"Page count: {page_count}, Description length: {len(description)}")

    return results