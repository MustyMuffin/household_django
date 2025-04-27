from accounts.models import UserStats
from accounts.xp_utils import XPManager

def user_xp_data(request):
    if request.user.is_authenticated:
        stats = UserStats.objects.filter(user=request.user).first()
        if stats:
            xp = stats.xp
            level = stats.level
            next_level_xp = XPManager.next_level_xp(level)
            xp_to_next = XPManager.xp_to_next_level(xp, level)
            progress_percent = XPManager.progress_percent(xp, level)
        else:
            xp = 0
            level = 1
            next_level_xp = 100
            xp_to_next = 100
            progress_percent = 0
    else:
        xp = 0
        level = 1
        next_level_xp = 100
        xp_to_next = 100
        progress_percent = 0

    return {
        'user_level': level,
        'xp': xp,
        'next_level_xp': next_level_xp,
        'xp_to_next': xp_to_next,
        'progress_percent': progress_percent,
    }