from django.contrib import messages
from accounts.models import UserStats
from book_club.models import WordsRead
from chores.models import ChoreEntry


def check_and_award_badges(user):
    from accounts.models import Badge, UserBadge

    stats = UserStats.objects.get(user=user)
    words_read = WordsRead.objects.filter(user=user).first()
    chores_done = ChoreEntry.objects.filter(user=user).count()

    badges = Badge.objects.all()

    for badge in badges:
        already_awarded = UserBadge.objects.filter(user=user, badge=badge).exists()
        if already_awarded:
            continue

        # Conditions
        meets_xp = stats.xp >= badge.xp_required
        meets_words = words_read and (words_read.wordsLifetime >= badge.words_required)
        meets_chores = chores_done >= badge.chores_completed_required

        if meets_xp or meets_words or meets_chores:
            UserBadge.objects.create(user=user, badge=badge)
            messages.success(
                None,
                f"🏅 Congratulations! You unlocked the badge: {badge.name}!"
            )