from decimal import Decimal
from .models import ChoreEntry, EarnedWage
from accounts.xp_helpers import award_xp
from accounts.badge_helpers import check_and_award_badges
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncWeek


def process_chore_completion(user, chore, request=None, form=None):
    """
    Handles XP, wage tracking, and badge awarding for a completed chore.
    Expects a Chore instance, and optionally a pre-bound form.
    Returns (entry, result, redirect_url, success).
    """
    if form and not form.is_valid():
        return None, None, None, False

    if form:
        entry = form.save(commit=False)
    else:
        entry = ChoreEntry()

    entry.chore = chore
    entry.user = user
    entry.wage = chore.wage
    entry.save()

    # Update earnings
    earned_wage, _ = EarnedWage.objects.get_or_create(user=user)
    earned_wage.earnedLifetime += Decimal(chore.wage)
    earned_wage.earnedSincePayout += Decimal(chore.wage)
    earned_wage.save()

    # Badges
    current_count = ChoreEntry.objects.filter(user=user, chore=chore).count()
    if request:
        check_and_award_badges(user, "chores", chore.name, current_count, request)
        check_and_award_badges(user, "chores", "earned_wage", chore.wage, request)


    # XP
    result = award_xp(
        user=user,
        source_object=chore,
        reason=f"Completed chore: {chore.name}",
        source_type="chore",
        request=request
    )

    redirect_url = reverse("chores:chores_by_category")
    return entry, result, redirect_url, True

def get_chore_stats_days(timeframe_days=7, chore=None):
    """
    Returns aggregated chore statistics for the past `timeframe_days` days.
    If `chore` is provided, filters entries by that chore.
    """
    now = timezone.now()
    cutoff = now - timedelta(days=timeframe_days)

    recent_entries = ChoreEntry.objects.filter(date_added__gte=cutoff)
    if chore:
        recent_entries = recent_entries.filter(chore=chore)

    top_users = (
        recent_entries
        .values('user__id', 'user__username')
        .annotate(total_done=Count('id'), total_wage=Sum('wage'))
        .order_by('-total_done')
    )

    top_chores = (
        recent_entries
        .values('chore__id', 'chore__name')
        .annotate(times_done=Count('id'))
        .order_by('-times_done')
    )

    user_chore_breakdown = (
        recent_entries
        .values('user__username', 'chore__name')
        .annotate(times_done=Count('id'), total_wage=Sum('wage'))
        .order_by('user__username', '-times_done')
    )

    per_day_breakdown = (
        recent_entries
        .annotate(day=TruncDate('date_added'))
        .values('day', 'user__username')
        .annotate(times_done=Count('id'), total_wage=Sum('wage'))
        .order_by('day', 'user__username')
    )

    return {
        "top_users": list(top_users),
        "top_chores": list(top_chores),
        "user_chore_breakdown": list(user_chore_breakdown),
        "per_day_breakdown": list(per_day_breakdown),
        "range_start": cutoff,
        "range_end": now,
    }