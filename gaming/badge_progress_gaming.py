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

@BadgeProgressProvider.register("gaming")
def check_all_collectibles_found(user, game):
    types = CollectibleType.objects.filter(game=game)
    for t in types:
        progress = UserCollectibleProgress.objects.filter(user=user, collectible_type=t).first()
        if not progress or progress.collected < t.total_available:
            return  # Not done yet

    # All collected
    badge = Badge.objects.filter(app_label="gaming", milestone_type="all_collectibles", game=game).first()
    if badge:
        UserBadge.objects.get_or_create(user=user, badge=badge)

@BadgeProgressProvider.register("gaming")
def get_game_completion_combo_progress(badge, user):
    if not badge.milestone_type.startswith("game_completion_combo_"):
        return 0  # Not a combo badge

    try:
        game_id = int(badge.milestone_type.split("_")[-1])
        game = Game.objects.get(id=game_id)
    except (ValueError, Game.DoesNotExist):
        return 0

    # Check all conditions
    hours = GameProgress.objects.filter(user=user, game=game).first()
    has_hours = hours and hours.hours_played >= badge.milestone_value

    has_beaten = GamesBeaten.objects.filter(user=user, game=game).exists()

    types = CollectibleType.objects.filter(game=game)
    has_all_collectibles = all(
        UserCollectibleProgress.objects.filter(user=user, collectible_type=t).first() and
        UserCollectibleProgress.objects.get(user=user, collectible_type=t).collected >= t.total_available
        for t in types
    )

    if has_beaten and has_all_collectibles and has_hours:
        return 100
    return 0

