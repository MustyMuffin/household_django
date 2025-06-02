from django.core.management.base import BaseCommand
from django.conf import settings
from gaming.models import RetroConsole
import requests

API_BASE = "https://retroachievements.org/API"

class Command(BaseCommand):
    help = "Fetch and store RetroAchievements console list"

    def handle(self, *args, **options):
        try:
            response = requests.get(f"{API_BASE}/API_GetConsoleIDs.php", params={
                "z": settings.RETROACHIEVEMENTS_USER,
                "y": settings.RETROACHIEVEMENTS_API_KEY,
            })
            data = response.json()

            if not isinstance(data, list):
                self.stderr.write("❌ Unexpected response format:")
                self.stderr.write(str(data))
                return

            for console in data:
                console_id = int(console["ID"])
                name = console["Name"]

                obj, created = RetroConsole.objects.update_or_create(
                    console_id=console_id,
                    defaults={"name": name}
                )

                status = "🆕 Created" if created else "↻ Updated"
                self.stdout.write(f"{status}: {name} (ID: {console_id})")

            self.stdout.write(f"✅ {len(data)} consoles cached.")

        except Exception as e:
            self.stderr.write(f"❌ Error: {e}")
