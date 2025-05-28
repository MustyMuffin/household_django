import requests
import time
from django.conf import settings
from gaming.models import TrueAchievementsGameCache

APIFY_TOKEN = settings.APIFY_TOKEN
ACTOR_ID = "mustymuffin~trueachievements-games-scraper-task"
API_BASE = "https://api.apify.com/v2"
MAX_WAIT_SECONDS = 90
POLL_INTERVAL = 3  # seconds

def fetch_game_data_trueachievements(title):
    # 1. Trigger the Apify actor with search
    run = requests.post(
        f"{API_BASE}/actor-tasks/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        json={"search": title}
    ).json()

    run_id = run.get("data", {}).get("id")
    if not run_id:
        print("❌ Could not start Apify actor.")
        return None

    # 2. Poll for completion
    for _ in range(MAX_WAIT_SECONDS // POLL_INTERVAL):
        run_status = requests.get(f"{API_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}").json()
        if run_status["data"]["status"] == "SUCCEEDED":
            dataset_id = run_status["data"]["defaultDatasetId"]
            break
        elif run_status["data"]["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"❌ Actor run failed with status: {run_status['data']['status']}")
            return None
        time.sleep(POLL_INTERVAL)

    if not dataset_id:
        print("❌ Apify actor run timed out.")
        return None

    # 3. Get results
    items = requests.get(f"{API_BASE}/datasets/{dataset_id}/items?token={APIFY_TOKEN}").json()

    if not isinstance(items, list) or not items:
        print("❌ No items found or unexpected format.")
        return None

    results = []
    for game in items[:5]:
        results.append({
            "title": game.get("title", ""),
            "description": game.get("description", ""),
            "image": game.get("image", ""),
            "achievements": game.get("achievements", []),
            "source": "trueachievements",
            "id": game.get("id", ""),
        })

        TrueAchievementsGameCache.objects.update_or_create(
            ta_id=game.get("id", ""),
            defaults={
                "title": game.get("title", ""),
                "image_url": game.get("image", ""),
                "data": game,
            }
        )


    return {"results": results}


