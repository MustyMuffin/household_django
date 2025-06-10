from collections import defaultdict
from difflib import get_close_matches
from difflib import get_close_matches
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from urllib.parse import quote_plus

from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from gaming.api.howlongtobeat_fetcher import fetch_hltb_data
from gaming.api.retroachievements import fetch_game_data_retro, fetch_achievements_for_game
from gaming.api_combined import fetch_game_data
from gaming.utils import update_badges_for_games, get_game_links
from .forms import GameEntryForm, GameForm, GameProgressTrackerForm, CollectibleTypeForm
from .models import Game, GameCategory, GameLink, RetroGameEntry
from .models import (Game, GamesBeaten, GameCategory,
                     IGDBGameCache, TrueAchievementsGameCache,
                     GameProgress, CollectibleType,
                     UserCollectibleProgress, GameLink, RetroGameCache,
                     RetroGameEntry
                     )

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

def achievements_view(request):
    data = get_trueachievements_data()
    return render(request, "gaming/achievements.html", {"achievements": data})


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


@login_required
def log_game_progress(request, game_id):
    print("✅ Entered log_game_progress view")

    game = get_object_or_404(Game, id=game_id)
    progress_entry = GameProgress.objects.filter(user=request.user, game=game).first()
    already_beaten = GamesBeaten.objects.filter(user=request.user, game_name=game.name).exists()

    if request.method == 'POST':
        print("📝 POST data:", request.POST.dict())

        old_hours = progress_entry.hours_played if progress_entry else 0
        previously_beaten = progress_entry.beaten if progress_entry else False

        form = GameProgressTrackerForm(request.POST, instance=progress_entry)

        if form.is_valid():
            new_hours = form.cleaned_data['hours_played']
            beaten = form.cleaned_data.get('beaten', False)
            note = form.cleaned_data.get('note', '')

            delta = new_hours - old_hours
            print(f"📊 Old hours: {old_hours}, New hours: {new_hours}, Delta: {delta}")
            print("DEBUG beaten:", beaten)

            was_new_entry = not progress_entry  # Track if this is a new GameProgress

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

            # # ✅ New logic — populate achievements for new tracking
            # if was_new_entry and game.retro_game:
            #     populate_user_achievements(request.user, progress_entry)
            #     print("🎯 User achievements populated for new progress entry.")

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

            for collectible_type in game.collectible_types.all():
                field_name = f"collectible_{collectible_type.id}"
                if field_name in request.POST:
                    try:
                        collected = int(request.POST.get(field_name))
                        progress, _ = UserCollectibleProgress.objects.get_or_create(
                            user=request.user,
                            collectible_type=collectible_type
                        )
                        progress.collected = collected
                        progress.save()
                    except (ValueError, TypeError):
                        continue

            check_and_award_badges(
                user=request.user,
                app_label="gaming",
                milestone_type=f"game_completion_combo_{game.id}",
                current_value=new_hours,
                request=request,
            )

            update_badges_for_games(user=request.user, game=game, hours_increment=delta, request=request)

            return redirect("gaming:games_by_category")
        else:
            print("❌ Form errors:", form.errors)
            messages.error(request, "❌ Invalid input. Please check your form.")
    else:
        form = GameProgressTrackerForm(instance=progress_entry)

    user_collectibles = {
        c.collectible_type.id: c.collected for c in
        UserCollectibleProgress.objects.filter(user=request.user, collectible_type__game=game)
    }

    already_mastered = GameProgress.objects.filter(
        user=request.user, game=game, mastered=True
    ).exists()
    print ("debug: already_mastered:", already_mastered)

    return render(request, "gaming/log_game_progress.html", {
        "form": form,
        "game": game,
        "is_update": bool(progress_entry),
        "already_beaten": already_beaten,
        "already_mastered": already_mastered,
        "user_collectibles": user_collectibles,
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
        user=request.user, beaten=False, mastered=False,
    )
    beaten_games = GameProgress.objects.select_related('game').filter(
        user=request.user, beaten=True, mastered=False,
    )
    mastered_games = GameProgress.objects.select_related('game').filter(
        user=request.user, mastered=True, beaten=True,
    )

    return render(request, 'gaming/game_backlog.html', {
        'in_progress_games': in_progress_games,
        'beaten_games': beaten_games,
        'mastered_games': mastered_games,
    })

@login_required
@user_passes_test(is_privileged)
def add_new_game(request):
    categories = GameCategory.objects.all()

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        new_category_name = request.POST.get("new_category_name", "").strip()
        image = request.POST.get("image_url", "").strip()
        selected_sources = request.POST.getlist("sources")
        print("Debug: selected_sources:", selected_sources)

        # ✅ Auto-toggle use_retro based on source selection
        use_retro = "retroachievements" in selected_sources
        print("Debug: use_retro:", use_retro)

        # ✅ Determine category
        if new_category_name:
            category, _ = GameCategory.objects.get_or_create(name=new_category_name)
        elif category_id.isdigit():
            category = GameCategory.objects.filter(id=category_id).first()
        else:
            category = None

        if not category:
            messages.error(request, "❌ Please select or create a category.")
            return render(request, "gaming/add_new_game.html", {
                "categories": categories,
                "preserve_title": title,
                "preserve_image": image,
                "preserve_sources": selected_sources,
                "preserve_category_id": category_id,
                "preserve_new_category_name": new_category_name,
            })

        # ✅ Create game
        game = Game.objects.create(
            name=title,
            game_category=category,
            image_url=image,
        )

        request.session["selected_sources"] = selected_sources

        # ✅ Fill hours HowLongToBeat
        auto_fill_game_hours(game)

        # ✅ RetroAchievements pairing step
        if use_retro and not game.retro_game:
            all_titles = list(RetroGameEntry.objects.values_list("title", flat=True))
            close_titles = get_close_matches(game.name, all_titles, n=20, cutoff=0.6)
            matches = RetroGameEntry.objects.filter(title__in=close_titles)

            messages.info(request, "Please pair your game with a RetroAchievements entry.")
            request.session["selected_sources"] = selected_sources
            request.session["retro_matches"] = [m.id for m in matches]  # optional
            return redirect("gaming:retro_pairing", game_id=game.id)

        # ✅ Redirect if no pairing required
        messages.success(request, f"🎮 Game '{game.name}' added with {len(selected_sources)} achievement links!")
        return redirect("gaming:generate_game_links", game_id=game.id)

    return render(request, "gaming/add_new_game.html", {"categories": categories})

@login_required
def retro_pairing(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    # Always fetch fresh matches based on current game's name
    all_titles = list(RetroGameEntry.objects.values_list("title", flat=True))
    close_titles = get_close_matches(game.name, all_titles, n=20, cutoff=0.6)
    matches = RetroGameEntry.objects.filter(title__in=close_titles)

    selected_sources = request.session.get("selected_sources", [])

    if request.method == "POST" and "pair_ra_game" in request.POST:
        selected_id = request.POST.get("retro_id")
        manual_id = request.POST.get("manual_retro_id", "").strip()
        final_id = manual_id if manual_id else selected_id

        match = RetroGameEntry.objects.filter(id=final_id).first()
        if match:
            game.retro_game = match
            game.save()

            # Add RA link with updated retro_id
            links = get_game_links(game.name, retro_id=match.retro_id)
            if "retroachievements" in links:
                GameLink.objects.get_or_create(
                    game=game,
                    platform="retroachievements",
                    defaults={"url": links["retroachievements"]}
                )

        return redirect("gaming:generate_game_links", game_id=game.id)

    # GET request: show recomputed matches only
    return render(request, "gaming/retro_pairing.html", {
        "game": game,
        "matches": matches,
        "selected_sources": selected_sources,
    })


@login_required
@user_passes_test(is_privileged)
def unpair_retro_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.method == "POST":
        game.retro_game = None
        game.save()

        # Optionally delete the existing RA link
        GameLink.objects.filter(game=game, platform="retroachievements").delete()

        messages.success(request, "❌ Unpaired RetroAchievements game.")

    return redirect("gaming:game_detail", game_id=game.id)

@login_required
@user_passes_test(is_privileged)
def generate_game_links(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    selected_sources = request.session.get("selected_sources", [])
    print("DEBUG (generate_game_links): selected_sources =", selected_sources)

    if not selected_sources:
        messages.warning(request, "⚠️ No sources selected for link generation.")
        return redirect("gaming:game_detail", game_id=game.id)

    links = get_game_links(game.name, retro_id=game.retro_game.retro_id if game.retro_game else None)

    created_or_updated = 0
    for source in selected_sources:
        if source in links:
            link_obj, created = GameLink.objects.update_or_create(
                game=game,
                platform=source,
                defaults={"url": links[source]}
            )
            print("DEBUG (generate_game_links): Created or updated link for", source)
            if created or link_obj.url != links[source]:
                created_or_updated += 1

            messages.success(request, f"Achievement links created or updated!")

    return redirect("gaming:game_detail", game_id=game.id)


@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    collectible_types = game.collectible_types.all()
    latest_progress = GameProgress.objects.filter(game=game, user=request.user).first()

    # User's collectible progress
    user_progress = {
        progress.collectible_type.id: progress.collected
        for progress in UserCollectibleProgress.objects.filter(
            user=request.user,
            collectible_type__in=collectible_types
        )
    }

    # Handle collectible type creation
    collectible_form = CollectibleTypeForm()
    if request.method == 'POST' and "add_collectible_type" in request.POST:
        collectible_form = CollectibleTypeForm(request.POST)
        if collectible_form.is_valid():
            new_type = collectible_form.save(commit=False)
            new_type.game = game
            new_type.save()
            messages.success(request, f"✅ Added collectible type: {new_type.name}")
            return redirect("gaming:game_detail", game_id=game.id)
        else:
            messages.error(request, "❌ Error adding collectible type. Please check your input.")

    # Privilege check
    is_privileged = request.user.is_superuser or request.user.groups.filter(name="Privileged").exists()

    # Achievement links
    achievement_links = game.links.all()

    return render(request, "gaming/game_detail.html", {
        "game": game,
        "description": None,
        "achievement_links": achievement_links,
        "user_collectibles": user_progress,
        "collectible_form": collectible_form,
        "is_privileged": is_privileged,
        "progress": latest_progress,
    })

@login_required
@user_passes_test(is_privileged)
def add_link_source(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    source = request.POST.get("source")

    if source == "retroachievements":
        # Save selected source and redirect to pairing
        request.session["selected_sources"] = ["retroachievements"]
        messages.info(request, "🕹️ Please pair your game with a RetroAchievements entry.")
        return redirect("gaming:retro_pairing", game_id=game.id)

    # Generate normal links
    request.session["selected_sources"] = [source]
    return redirect("gaming:generate_game_links", game_id=game.id)

def auto_fill_game_hours(game: Game):
    data = fetch_hltb_data(game.name)
    if data:
        game.hours_main_story = data["hours_main_story"]
        game.hours_main_extra = data["hours_main_extra"]
        game.hours_completionist = data["hours_completionist"]
        game.save()
        print(f"📊 Updated hours for {game.name}")

def find_retro_matches(title, limit=5):
    all_titles = list(RetroGameEntry.objects.values_list('title', flat=True))
    close_titles = difflib.get_close_matches(title, all_titles, n=limit, cutoff=0.6)

    return RetroGameEntry.objects.filter(title__in=close_titles)

@login_required
@user_passes_test(is_privileged)
def remove_game_link(request, game_id, link_id):
    game = get_object_or_404(Game, id=game_id)
    link = get_object_or_404(GameLink, id=link_id, game=game)

    link.delete()
    messages.success(request, f"🗑️ Removed link for {link.platform.capitalize()}.")

    return redirect("gaming:game_detail", game_id=game.id)