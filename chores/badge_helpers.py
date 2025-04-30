from accounts.badge_mixins import BadgeAwardMixin

class ChoreBadgeChecker(BadgeAwardMixin):
    def check_and_award(self, user, chore_slug, total_completed):
        self.award_badges(user, milestone_type=chore_slug, current_value=total_completed)
