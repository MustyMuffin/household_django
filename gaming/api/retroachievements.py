import requests
import difflib
from django.conf import settings
from gaming.models import RetroGameCache

API_BASE = "https://retroachievements.org/API"

def fetch_game_data_retro(title, progress_user=None):
    """Fetch RetroAchievements game metadata and user progress."""
    api_key = settings.RETROACHIEVEMENTS_API_KEY
    progress_user = progress_user or settings.RETROACHIEVEMENTS_USER

    # Step 1: Get all games using new params (no username needed)
    try:
        response = requests.get(f"{API_BASE}/API_GetGameList.php", params={
            "y": api_key,
            "i": 1,
            "h": 1,
            "f": 1,
        })
        all_games = response.json()

        if not isinstance(all_games, list):
            raise ValueError("RA API did not return a list")

        # Filter to titles containing the first word of search input
        keyword = title.lower().split()[0]
        filtered_games = [g for g in all_games if keyword in g["Title"].lower()]
        titles = [g["Title"] for g in filtered_games]

        close_titles = difflib.get_close_matches(title, titles, n=5, cutoff=0.65)
        print("🎯 Close matches:", close_titles)

    except Exception as e:
        print("🚨 Error in fetch_game_data_retro:", e)
        return None

    # Step 2: Try each close match until one returns a valid result
    for t in close_titles:
        match = next((g for g in filtered_games if g["Title"] == t), None)
        if not match:
            continue

        game_id = int(match["ID"])

        # Try to fetch full info
        try:
            info = requests.get(f"{API_BASE}/API_GetGameInfoAndUser.php", params={
                "y": api_key,
                "u": progress_user,
                "g": game_id,
            }).json()

            if not isinstance(info, dict) or not info.get("Title"):
                print(f"⚠ Skipped invalid match '{t}' — response:", info)
                continue

            # Cache if not already stored
            if not RetroGameCache.objects.filter(retro_id=game_id).exists():
                RetroGameCache.objects.create(
                    retro_id=game_id,
                    title=info.get("Title", ""),
                    console=info.get("ConsoleName", ""),
                    image_url=info.get("ImageIcon", ""),
                    data=info,
                )

            return _format_game(info)

        except Exception as e:
            print(f"❌ Error retrieving info for '{t}':", e)

    print(f"🔍 No valid match found for '{title}' after trying close titles.")
    return None


def _format_game(data):
    """Normalize the data format returned by RA."""
    return {
        "title": data.get("Title", ""),
        "description": f"{data.get('ConsoleName')} game from RetroAchievements",
        "image": data.get("ImageIcon", ""),
        "achievements": data.get("Achievements", {}),
        "source": "retroachievements",
    }
