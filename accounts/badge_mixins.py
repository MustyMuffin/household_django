from .models import Badge, UserBadge

class BadgeAwardMixin:
    def award_badges(self, user, milestone_type, current_value):
        """
        Checks for eligible badges by milestone type and value.
        """
        eligible = Badge.objects.filter(
            milestone_type=milestone_type,
            milestone_value__lte=current_value,
        ).exclude(userbadge__user=user)

        for badge in eligible:
            UserBadge.objects.create(user=user, badge=badge)

class BadgeProgressMixin:
    def is_complete(self):
        return self.progress >= 100

    def progress_percent(self):
        return min(100, int(self.progress))