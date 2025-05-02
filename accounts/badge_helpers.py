from django.utils.timezone import now
from django.contrib import messages

def check_and_award_badges(user, app_label, milestone_key, current_value, request=None):
    # Move imports here to avoid circular import at module level
    from accounts.models import UserBadge, Badge

    unlocked_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    eligible_badges = Badge.objects.filter(
        app_label=app_label,
        milestone_type=milestone_key,
        milestone_value__lte=current_value
    ).exclude(id__in=unlocked_badges)

    for badge in eligible_badges:
        UserBadge.objects.create(user=user, badge=badge, awarded_at=now())
        if request:
            messages.success(request, f"🏅 Badge Unlocked!: {badge.name}")

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
