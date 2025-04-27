from .models import UserStats, XPSettings


def get_user_stats(user):
    stats = UserStats.objects.filter(user=user).first()

    if stats:
        user_level = stats.level
        xp = stats.xp
        next_level_xp = stats.next_level_xp()
        progress_percent = stats.progress_percent()
    else:
        user_level = 1
        xp = 0
        next_level_xp = 100
        progress_percent = 0

    return {
        'user_level': user_level,
        'xp': xp,
        'next_level_xp': next_level_xp,
        'progress_percent': progress_percent,
    }