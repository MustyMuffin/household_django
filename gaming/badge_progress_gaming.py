from gaming.models import GamesBeaten
from accounts.models import UserStats
from accounts.badge_helpers import BadgeProgressProvider

@BadgeProgressProvider.register("gaming")
def get_games_progress(badge, user):
    count = GamesBeaten.objects.filter(user=user).count()
    return min(int((count / badge.milestone_value) * 100), 100)

@BadgeProgressProvider.register("gaming")
def get_hours_played_progress(badge, user):
    try:
        count = UserStats.objects.get(user=user).hours_played
        return min(int((count / badge.milestone_value) * 100), 100)
    except UserStats.DoesNotExist:
        return 0
