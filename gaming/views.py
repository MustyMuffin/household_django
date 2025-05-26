from django.shortcuts import render
from django.core.cache import cache
from collections import defaultdict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from gaming.utils import update_badges_for_games
from accounts.badge_helpers import check_and_award_badges
from accounts.xp_helpers import award_xp
from .forms import GameEntryForm, GameForm, GameProgressTrackerForm
from .models import Game, GameProgressTracker
from accounts.models import UserStats
from django.contrib.auth.decorators import user_passes_test

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

def achievements_view(request):
    data = get_trueachievements_data()
    return render(request, "gaming/achievements.html", {"achievements": data})


def get_trueachievements_data():
    if (cached := cache.get("ta_data")) is not None:
        return cached
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cache.set("ta_data", data, 60 * 10)  # cache for 10 mins
        return data
    return []

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

def log_hours(user, hours, game, request):
    hours_entry, _ = UserStats.objects.get_or_create(user=user)
    hours_entry.hours_played += hours
    hours_entry.save()

    result = award_xp(
        user=user,
        source_object=hours,
        reason=f"💾 Progress in '{game.name}'",
        source_type="game_partial",
        request=request,
    )

    if result.get('xp_awarded'):
        messages.success(request, f"✅ You earned {result['xp_awarded']} XP for game progress!")

    update_badges_for_games(user=user, game=game, hours_increment=hours, request=request)


@login_required
def new_game_entry(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    form = GameEntryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        tracker = GameProgressTracker.objects.filter(user=request.user, game_name=game).first()

        if tracker:
            remaining_hours = max(game.hours - tracker.hours_completed, 0)
            tracker.delete()
            log_hours(request.user, remaining_hours, game, request)
        else:
            award_xp(request.user, source_object=game, reason=f"Logged game: {game.name}", source_type="game", request=request)

        form.instance.game = game
        form.instance.user = request.user
        form.save()

        bonus_result = award_xp(request.user, source_object=game, reason="🎮 Completed game bonus", source_type="finished_game", request=request)

        if bonus_result.get('xp_awarded'):
            messages.success(request, f"✅ Bonus XP: {bonus_result['xp_awarded']} for finishing a game!")

        update_badges_for_games(user=request.user, game=game, hours_increment=game.hours, request=request)

        return redirect('gaming:games_by_category')

    return render(request, 'gaming/new_game_entry.html', {'game': game, 'form': form})


@login_required
def new_game_tracker_entry(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    existing_entry = GameProgressTracker.objects.filter(user=request.user, game_name=game).first()

    if existing_entry and request.method != 'POST':
        messages.warning(request, "You've already logged progress for this game.")
        return redirect('gaming:update_game_tracker_entry', pk=existing_entry.pk)

    form = GameProgressTrackerForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        hours = int(form.cleaned_data['hours_completed'])

        form.instance.game_name = game
        form.instance.user = request.user
        form.instance.hours_completed = hours
        form.save()

        log_hours(request.user, hours, game, request)
        return redirect('gaming:games_by_category')

    return render(request, 'gaming/new_game_tracker_entry.html', {'form': form, 'game': game})


@login_required
def update_game_tracker_entry(request, pk):
    entry = get_object_or_404(GameProgressTracker, pk=pk, user=request.user)
    game = entry.game_name
    old_hours = entry.hours_completed

    print('DEBUG: entry = ', entry)
    print('DEBUG: game = ', game)
    print('DEBUG: old_hours = ', old_hours)

    form = GameProgressTrackerForm(request.POST or None, instance=entry)

    if request.method == 'POST' and form.is_valid():
        new_hours = form.cleaned_data['hours_completed']
        print('DEBUG: new_hours = ', new_hours)
        progress = new_hours - old_hours
        print('DEBUG: progress = ', progress)
        form.save()

        if progress > 0:
            log_hours(request.user, progress, game, request)

        messages.success(request, f"✅ Updated progress for '{game}'")
        return redirect('gaming:games_by_category')

    return render(request, 'gaming/update_game_tracker_entry.html', {'form': form, 'game': game})


@login_required
def game_backlog(request):
    in_progress_games = GameProgressTracker.objects.select_related('game_name').filter(
        user=request.user,
        hours_completed__gt=0,
    ).exclude(hours_completed__gte=F('game_name__hours'))

    return render(request, 'gaming/game_backlog.html', {
        'in_progress_games': in_progress_games
    })


@user_passes_test(is_privileged)
def add_new_game(request):
    """Add a new game (privileged users only)."""
    if request.method == 'POST':
        form = GameForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('gaming:games_by_category')
    else:
        form = GameForm()

    return render(request, 'gaming/add_new_game.html', {'form': form})