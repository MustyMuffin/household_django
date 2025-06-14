import requests
import difflib
from django.conf import settings
from gaming.models import RetroGameCache, UserGameAchievement, RetroGameEntry

API_BASE = "https://retroachievements.org/API"

def fetch_game_data_retro(title, console_id=1, progress_user=None):
    """Fetch RetroAchievements metadata using pre-cached game list from your DB."""
    from django.conf import settings
    import requests

    API_BASE = "https://retroachievements.org/API"
    api_key = settings.RETROACHIEVEMENTS_API_KEY
    progress_user = progress_user or settings.RETROACHIEVEMENTS_USER

    # Step 1: Search prepopulated local game list
    keyword = title.lower().split()[0]
    filtered_games = RetroGameEntry.objects.filter(
        console_id=console_id,
        title__icontains=keyword
    )

    titles = [g.title for g in filtered_games]
    close_titles = difflib.get_close_matches(title, titles, n=5, cutoff=0.65)
    # print("🎯 Close matches:", close_titles)

    # Step 2: Try each match
    for t in close_titles:
        match = filtered_games.filter(title=t).first()
        if not match:
            continue

        game_id = int(match.retro_id)

        # Skip if already cached
        if RetroGameCache.objects.filter(retro_id=game_id).exists():
            # print(f"✅ Already cached: {match.title}")
            return RetroGameCache.objects.get(retro_id=game_id)

        # Fetch game + achievements from RA API
        try:
            info = requests.get(f"{API_BASE}/API_GetGameInfoAndUser.php", params={
                "y": api_key,
                "u": progress_user,
                "g": game_id,
            }).json()

            if not isinstance(info, dict) or not info.get("Title"):
                # print(f"⚠ Invalid data for match '{t}':", info)
                continue

            formatted = _format_game(info)

            cache_entry, _ = RetroGameCache.objects.update_or_create(
                retro_id=game_id,
                defaults={
                    "title": formatted["title"],
                    "console": info.get("ConsoleName", ""),
                    "image_url": formatted["image"],
                    "data": formatted,
                    "achievements": formatted["achievements"],
                },
            )

            return cache_entry

        except Exception as e:
            print(f"❌ Error retrieving RA info for '{t}':", e)

    # print(f"🔍 No valid match found for '{title}' in local cache.")
    return None


def _format_game(data):
    """Normalize the data format returned by RA."""
    achievements_raw = data.get("Achievements", {})
    achievements = []

    for ach in achievements_raw.values():
        achievements.append({
            "id": ach.get("ID"),
            "title": ach.get("Title"),
            "description": ach.get("Description"),
            "points": ach.get("Points"),
            "badge_url": ach.get("BadgeURL"),
            "date_earned": ach.get("DateEarned"),
        })

    return {
        "title": data.get("Title", ""),
        "description": f"{data.get('ConsoleName')} game from RetroAchievements",
        "image": data.get("ImageIcon", ""),
        "achievements": achievements,
        "source": "retroachievements",
    }

def fetch_achievements_for_game(retro_id):
    api_key = settings.RETROACHIEVEMENTS_API_KEY
    username = settings.RETROACHIEVEMENTS_USER

    try:
        user_url = f"{API_BASE}/API_GetGameInfoAndUser.php"
        params = {"y": api_key, "u": username, "g": int(retro_id)}
        # print(f"📤 Request URL: {user_url}?{params}")
        response = requests.get(user_url, params=params)
        # print(f"📥 Status Code: {response.status_code}")
        # print("📦 Raw Response:", response.text)

        # Retry with non-user endpoint if 404
        if response.status_code == 404:
            # print("🔁 Falling back to non-user API endpoint")
            fallback_url = f"{API_BASE}/API_GetGame.php"
            response = requests.get(fallback_url, params={"y": api_key, "g": int(retro_id)})
            # print(f"📥 Status Code: {response.status_code}")
            # print("📦 Raw Response:", response.text)

        data = response.json()

        if not isinstance(data, dict) or not data.get("Title"):
            print("❌ Failed to fetch RA achievements: No valid game data in response")
            return None

        achievements = data.get("Achievements") or {}
        if not isinstance(achievements, dict) or not achievements:
            print("❌ Failed to fetch RA achievements: No achievements found in API response")
            return None

        # Save achievements to DB
        for achievement in achievements.values():
            UserGameAchievement.objects.get_or_create(
                game=game,
                retro_id=retro_id,
                title=achievement.get("Title", "Untitled"),
                description=achievement.get("Description", ""),
                points=achievement.get("Points", 0),
                badge_url=achievement.get("BadgeName", ""),
            )

        return {
            "title": data.get("Title"),
            "console": data.get("ConsoleName"),
            "image": data.get("ImageIcon"),
            "achievements": list(achievements.values()),
            "raw": data,
        }

    except Exception as e:
        print("❌ Exception while fetching RA achievements:", e)
        return None
