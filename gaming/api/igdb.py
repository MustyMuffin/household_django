import requests
from django.conf import settings
from gaming.models import Game, IGDBGameCache

IGDB_BASE = "https://api.igdb.com/v4/games"

def get_igdb_token():
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def fetch_igdb_games(title):
    token = get_igdb_token()
    headers = {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    query = f'''
        search "{title}";
        fields name,summary,cover.url,first_release_date,genres.name;
        limit 5;
    '''
    response = requests.post(IGDB_URL, headers=headers, data=query)
    return response.json()

def format_time_to_beat(ttb):
    if not ttb:
        return None
    return {
        "hasty": ttb.get("hastly"),
        "normal": ttb.get("normally"),
        "complete": ttb.get("completely"),
    }

def fetch_game_data_igdb(title):
    token = get_igdb_token()
    if not token:
        print("❌ Failed to retrieve IGDB access token.")
        return None

    headers = {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    query = f'''
        search "{title}";
        fields name,summary,cover.url,aggregated_rating,first_release_date;
        limit 20;
    '''
    response = requests.post(IGDB_BASE, headers=headers, data=query)

    if response.status_code != 200:
        # print("❌ IGDB API error:", response.text)
        return None

    results = []
    for game in response.json():
        hours = 0  # Default for now

        IGDBGameCache.objects.update_or_create(
            igdb_id=game["id"],
            defaults={
                "title": game.get("name", ""),
                "description": game.get("summary", ""),
                "image_url": game.get("cover", {}).get("url", ""),
                "data": game,
            },
        )

        results.append({
            "title": game.get("name", ""),
            "description": game.get("summary", ""),
            "image": game.get("cover", {}).get("url", ""),
            "hours": hours,
            "id": game["id"],
            "source": "igdb",
        })

    return {"results": results}



