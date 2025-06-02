from django.core.management.base import BaseCommand
from django.conf import settings
from gaming.models import RetroGameEntry, RetroConsole
import requests

API_BASE = "https://retroachievements.org/API"

class Command(BaseCommand):
    help = "Fetch and cache all RetroAchievements games across supported consoles"

    def handle(self, *args, **options):
        api_key = settings.RETROACHIEVEMENTS_API_KEY
        username = settings.RETROACHIEVEMENTS_USER

        for console in RetroConsole.objects.all().order_by("console_id"):
            console_id = int(console.console_id)  # 🔥 FORCE INT HERE
            self.stdout.write(f"📦 Fetching console ID {console_id} ({console.name})...")

            try:
                response = requests.get(f"{API_BASE}/API_GetGameList.php", params={
                    "y": api_key,
                    "z": username,
                    "i": console_id,  # this must be an int, not string
                })
                data = response.json()
                print(f"🔍 Raw response for console ID {console_id}: {str(data)[:200]}")

                # Expecting a list of game dicts
                if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                    self.stderr.write(f"⚠ No valid game data for {console.name} (ID {console_id})")
                    continue

                for game in data:
                    RetroGameEntry.objects.update_or_create(
                        retro_id=game["ID"],
                        defaults={
                            "title": game["Title"],
                            "console_id": int(game["ConsoleID"]),
                            "console_name": game["ConsoleName"],
                            "image_url": game.get("ImageIcon", ""),
                        },
                    )

                self.stdout.write(f"✅ Cached {len(data)} games for {console.name}.")

            except Exception as e:
                self.stderr.write(f"❌ Error fetching for {console.name}: {e}")
