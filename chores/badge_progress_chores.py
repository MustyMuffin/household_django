from chores.models import ChoreEntry, Chore
from accounts.badge_helpers import BadgeProgressProvider

@BadgeProgressProvider.register("chores")
def get_chores_progress(badge, user):
    try:
        chore = Chore.objects.get(text=badge.milestone_type)
        count = ChoreEntry.objects.filter(user=user, chore=chore).count()
        return min(int((count / badge.milestone_value) * 100), 100)
    except Chore.DoesNotExist:
        return 0

