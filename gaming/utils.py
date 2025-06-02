from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from .models import GamesBeaten, GameProgress, UserGameAchievement, RetroGameCache
import re
from urllib.parse import quote_plus

def slugify_title(title):
    """
    Basic slugifier for URL-safe titles
    """
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip()).lower().strip("-")
    return slug

def get_game_links(title, retro_id):
    slug = slugify_title(title)
    query = quote_plus(title.strip())

    links = {
        "trueachievements": f"https://www.trueachievements.com/game/{slug}/achievements",
        "steam": f"https://store.steampowered.com/search/?term={query}",
        "playstation": f"https://www.playstationtrophies.org/search/?cx=partner-pub-3426976301179043%3A1869282366&cof=FORID%3A10&ie=UTF-8&q={query}",
    }

    if retro_id:
        links["retroachievements"] = f"https://retroachievements.org/game/{retro_id}"
        print("DEBUG: With RetroID triggered:", links)
    else:
        links["retroachievements"] = f"https://retroachievements.org/search/games/{query}"

    return links


def update_badges_for_games(user, game, hours_increment, request=None):
    # Get tracker record for the user and game
    tracker = GameProgress.objects.filter(user=user, game=game).first()

    # ✅ Only proceed with beaten logic if user explicitly marked it as beaten
    if not tracker or not tracker.beaten:
        return

    # Log game as beaten
    GamesBeaten.objects.get_or_create(user=user, game_name=game.name)

    # Badge checks
    games_beaten_total = GamesBeaten.objects.filter(user=user).count()
    hours_total = UserStats.objects.filter(user=user).first().hours_played

    check_and_award_badges(
        user=user,
        app_label="gaming",
        milestone_type="games_beaten",
        current_value=games_beaten_total,
        request=request
    )

    check_and_award_badges(
        user=user,
        app_label="gaming",
        milestone_type="hours_played",
        current_value=hours_total,
        request=request
    )

    # Update total hours
    userstats, _ = UserStats.objects.get_or_create(user=user)
    userstats.hours_played += hours_increment
    userstats.save(update_fields=["hours_played"])
