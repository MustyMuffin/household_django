from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from gaming.api.howlongtobeat_fetcher import fetch_hltb_data
from gaming.api_combined import fetch_game_data
from gaming.forms import GameProgressTrackerForm
from gaming.utils import update_badges_for_games
from .forms import GameEntryForm, GameForm, GameProgressTrackerForm

from .models import (Game, GamesBeaten, GameCategory,
                     IGDBGameCache, TrueAchievementsGameCache,
                     GameProgress
                    )


def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

def achievements_view(request):
    data = get_trueachievements_data()
    return render(request, "gaming/achievements.html", {"achievements": data})

# Optional: Remove @login_required if you want to allow anonymous access
def fetch_game_data_api(request):
    try:
        q = request.GET.get("q")
        source = request.GET.get("source")

        if not q or not source:
            return JsonResponse({"error": "Missing query or source"}, status=400)

        print(f"🔍 Fetching game: {q}, source: {source}")
        data = fetch_game_data(q, source)

        if not data or not data.get("results"):
            return JsonResponse({"error": "Game not found"}, status=404)

        return JsonResponse(data)


    except Exception as e:
        print("❌ fetch_game_data_api error:", e)
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)

def fetch_user_progress(request, game_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)

    ra_username = request.user.userstats.ra_username
    if not ra_username:
        return JsonResponse({"error": "No linked RetroAchievements username"}, status=400)

    api_key = settings.RETROACHIEVEMENTS_API_KEY
    system_user = settings.RETROACHIEVEMENTS_USER

    try:
        response = requests.get(f"{API_BASE}/API_GetGameInfoAndUser.php", params={
            "z": system_user,
            "y": api_key,
            "u": ra_username,
            "g": game_id,
        })
        progress_data = response.json()

        return JsonResponse(progress_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def games_by_category(request):
    # Group games by their category
    games_by_category = defaultdict(list)

    all_games = Game.objects.all()

    for item in all_games:
        category_name = item.game_category.name if item.game_category else "Uncategorized"
        games_by_category[category_name].append(item)

    context = {'games_by_category': dict(games_by_category), 'can_add_game': is_privileged(request.user)}
    return render(request, 'gaming/games_by_category.html', context)

def games(request):
    """Show all games."""
    games = game.objects.order_by('text')
    context = {'games': games}
    return render(request, 'gaming/games.html', context)

def game(request, game_id):
    """Show a single game and all its entries."""
    game = Game.objects.get(id=game_id)
    game_entries = game.gameentry_set.order_by('-date_added')
    context = {'game': game, 'game_entries': game_entries}
    return render(request, 'gaming/game.html', context)

@login_required
def log_game_progress(request, game_id):
    print("✅ Entered log_game_progress view")

    game = get_object_or_404(Game, id=game_id)
    progress_entry = GameProgress.objects.filter(user=request.user, game=game).first()
    already_beaten = GamesBeaten.objects.filter(user=request.user, game_name=game.name).exists()

    if request.method == 'POST':
        print("📝 POST data:", request.POST.dict())

        # Always capture old state before any modification
        old_hours = progress_entry.hours_played if progress_entry else 0
        previously_beaten = progress_entry.beaten if progress_entry else False

        form = GameProgressTrackerForm(request.POST, instance=progress_entry)

        if form.is_valid():
            new_hours = form.cleaned_data['hours_played']
            beaten = form.cleaned_data.get('beaten', False)
            note = form.cleaned_data.get('note', '')

            delta = new_hours - old_hours
            print(f"📊 Old hours: {old_hours}, New hours: {new_hours}, Delta: {delta}")

            if progress_entry:
                progress_entry.hours_played = new_hours
                progress_entry.beaten = beaten
                progress_entry.note = note
            else:
                progress_entry = form.save(commit=False)
                progress_entry.user = request.user
                progress_entry.game = game
                progress_entry.beaten = beaten
                progress_entry.note = note

            progress_entry.save()
            print("DEBUG: progress_entry.beaten =", progress_entry.beaten)

            if delta > 0:
                log_hours(request.user, delta, game, request)
                messages.success(request, f"💾 Logged {delta} new hours for '{game.name}'")

            if beaten and not previously_beaten:
                bonus_result = award_xp(
                    user=request.user,
                    source_object=game,
                    reason="🎯 Completed game bonus",
                    source_type="finished_game",
                    request=request,
                )
                print("🎁 Bonus result:", bonus_result)
                if bonus_result.get("xp_awarded"):
                    messages.success(request, f"✅ Bonus XP: {bonus_result['xp_awarded']} for finishing the game!")

            update_badges_for_games(user=request.user, game=game, hours_increment=delta, request=request)

            return redirect("gaming:games_by_category")
        else:
            print("❌ Form errors:", form.errors)
            messages.error(request, "❌ Invalid input. Please check your form.")
    else:
        form = GameProgressTrackerForm(instance=progress_entry)

    return render(request, "gaming/log_game_progress.html", {
        "form": form,
        "game": game,
        "is_update": bool(progress_entry),
        "already_beaten": already_beaten,
    })


def log_hours(user, hours_played, game, request=None):
    print(f"🔧 log_hours called with {hours_played} for '{game}'")

    userstats, _ = UserStats.objects.get_or_create(user=user)
    userstats.hours_played += hours_played
    userstats.save(update_fields=["hours_played"])

    # 👇 Add this print
    print("🎯 Calling award_xp...")
    result = award_xp(
        user=user,
        source_object=hours_played,
        reason=f"💾 Progress in '{game.name}'",
        source_type="game_partial",
        request=request,
    )

    # print("🎁 XP result:", result)

    if result.get('xp_awarded') and request:
        messages.success(request, f"✅ You earned {result['xp_awarded']} XP for game progress!")

    update_badges_for_games(user=user, game=game, hours_increment=hours_played, request=request)


@login_required
def game_backlog(request):
    in_progress_games = GameProgress.objects.select_related('game').filter(
        user=request.user,
        hours_played__gt=0,
    ).exclude(hours_played__gte=F('game__hours_completionist'))

    return render(request, 'gaming/game_backlog.html', {
        'in_progress_games': in_progress_games
    })

@login_required
@user_passes_test(is_privileged)
def add_new_game(request):
    categories = GameCategory.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        category_id = request.POST.get("category_id")
        image = request.POST.get("image_url")

        category = GameCategory.objects.filter(id=category_id).first()

        game = Game.objects.create(
            name=title,
            game_category=category,
            image_url=image,
        )

        auto_fill_game_hours(game)

        messages.success(request, f"🎮 Game '{game.name}' added!")
        return redirect("gaming:game_detail", game_id=game.id)

    return render(request, "gaming/add_new_game.html", {"categories": categories})

@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Try to find a cached metadata record
    cache = (
        IGDBGameCache.objects.filter(title=game.name).first()
        or TrueAchievementsGameCache.objects.filter(title=game.name).first()
        or RetroGameCache.objects.filter(title=game.name).first()
    )

    achievements = []
    description = None
    if cache and cache.data:
        data = cache.data
        description = cache.description or data.get("description") or data.get("summary")
        if isinstance(data.get("achievements"), list):
            achievements = data["achievements"]
        elif isinstance(data.get("Achievements"), dict):
            achievements = [v for k, v in data["Achievements"].items()]

    return render(request, "gaming/game_detail.html", {
        "game": game,
        "description": description,
        "achievements": achievements,
    })

def auto_fill_game_hours(game: Game):
    data = fetch_hltb_data(game.name)
    if data:
        game.hours_main_story = data["hours_main_story"]
        game.hours_main_extra = data["hours_main_extra"]
        game.hours_completionist = data["hours_completionist"]
        game.save()
        print(f"📊 Updated hours for {game.name}")