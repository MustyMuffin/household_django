from django.core.management.base import BaseCommand
from accounts.xp_utils import XPManager

class Command(BaseCommand):
    help = 'Debug XP Progression Curve'

    def add_arguments(self, parser):
        parser.add_argument('--max_level', type=int, default=50, help='Max level to test up to')

    def handle(self, *args, **options):
        max_level = options['max_level']

        self.stdout.write("\nXP Progression Debug Info:")
        self.stdout.write("Level | XP Required | XP to Next Level | Progress % (at Level Start)")
        self.stdout.write("-" * 70)

        for level in range(1, max_level + 1):
            xp_current = XPManager.xp_for_level(level)
            xp_next = XPManager.xp_for_level(level + 1)
            progress_at_start = XPManager.progress_percent(xp_current, level)

            self.stdout.write(
                f"{level:5} | {xp_current:11} | {xp_next - xp_current:15} | {progress_at_start:6}%"
            )

        self.stdout.write("\nDone.")
