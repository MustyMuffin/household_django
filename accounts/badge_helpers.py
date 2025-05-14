import traceback
from django.http import request
from django.utils.timezone import now
from django.contrib import messages

from book_club.models import BooksRead
from chores import models

class BadgeProgressProvider:
    registry = {}

    @classmethod
    def register(cls, app_label):
        def decorator(fn):
            cls.registry[app_label] = fn
            return fn

        return decorator

    @classmethod
    def get_progress(cls, badge, user):
        func = cls.registry.get(badge.app_label)
        if func:
            return func(badge, user)
        return 0

def check_and_award_badges(user, app_label, milestone_type, current_value, request=None):
    # Move imports here to avoid circular import at module level
    from accounts.models import UserBadge, Badge
    from django.db.models import Sum
    from chores.models import EarnedWage

    if milestone_type == "earned_wage":
        current_value = EarnedWage.objects.filter(user=user).aggregate(
            total=Sum('earnedLifetime')) ['total'] or 0

    # print(f"[DEBUG] Checking badges for user={user.username}, app_label={app_label}, milestone_type={milestone_type}, current_value={current_value}")

    # Get already unlocked badges
    unlocked_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    # print(f"[DEBUG] Already unlocked badge IDs: {list(unlocked_badges)}")

    # Filter for badges the user is eligible to unlock now
    eligible_badges = Badge.objects.filter(
        app_label=app_label,
        milestone_type=milestone_type,
        milestone_value__lte=current_value
    ).exclude(id__in=unlocked_badges)

    # print(f"[DEBUG] Eligible badges to unlock (count={eligible_badges.count()}): {[badge.name for badge in eligible_badges]}")

    for badge in eligible_badges:
        if current_value >= badge.milestone_value:

            UserBadge.objects.get_or_create(user=user, badge=badge)
            # print(f"[DEBUG] Unlocking badge: {badge.name}")

        if request:
            # print(f"[DEBUG] request is not None: {request}")
            messages.success(request, f"🏆 Badge Unlocked: {badge.name}!")
        else:
            # print("[DEBUG] No request passed to badge unlocker.")

            print(f"[DEBUG] Badge check complete for user={user.username}")