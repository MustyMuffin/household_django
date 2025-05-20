from decimal import Decimal
from .models import ChoreEntry, EarnedWage
from accounts.xp_helpers import award_xp
from accounts.badge_helpers import check_and_award_badges
from django.urls import reverse


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
        check_and_award_badges(user, "chores", chore.text, current_count, request)
        check_and_award_badges(user, "chores", "earned_wage", chore.wage, request)


    # XP
    result = award_xp(
        user=user,
        source_object=chore,
        reason=f"Completed chore: {chore.text}",
        source_type="chore",
        request=request
    )

    redirect_url = reverse("chores:chores_by_category")
    return entry, result, redirect_url, True
