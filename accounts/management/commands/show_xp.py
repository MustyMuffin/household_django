from django.core.management.base import BaseCommand
from accounts.models import UserStats
from accounts.xp_utils import XPManager

class Command(BaseCommand):
    help = 'Display XP, level, and progress % for all users.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("\nXP Overview for All Users:\n"))

        for stats in UserStats.objects.select_related('user'):
            username = stats.user.username
            xp = stats.xp
            level = XPManager.level_from_xp(xp)
            progress = XPManager.progress_percent(xp, level)
            xp_needed = XPManager.xp_to_next_level(xp, level)

            self.stdout.write(f"{username}: Level {level} | XP: {xp} | Progress: {progress}% | To-Go: {xp_needed}")

        self.stdout.write(self.style.SUCCESS("\nDone!"))