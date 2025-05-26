from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from .models import GamesPlayed, GameProgressTracker

def update_badges_for_games(user, game, hours_increment, request=None):
    # Only count as "played" if full progress is met
    tracker = GameProgressTracker.objects.filter(user=user, game_name=game).first()
    if tracker and tracker.hours_completed < game.hours:
        return

    GamesPlayed.objects.get_or_create(user=user, game_name=game.name)

    games_played_total = GamesPlayed.objects.filter(user=user).count()

    hours_total = UserStats.objects.filter(user=user).first().hours_played

    check_and_award_badges(
        user=user,
        app_label="gaming",
        milestone_type="games_played",
        current_value=games_played_total,
        request=request
    )
    check_and_award_badges(
        user=user,
        app_label="gaming",
        milestone_type="hours_played",
        current_value=hours_total,
        request=request
    )

    userstats, _ = UserStats.objects.get_or_create(user=user)
    userstats.hours_played += hours_increment
    userstats.save(update_fields=["hours_played"])