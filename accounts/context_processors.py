from accounts.models import UserStats, XPSettings
from accounts.xp_utils import XPManager

def user_xp_data(request):
    if not request.user.is_authenticated:
        return {}

    stats = UserStats.objects.filter(user=request.user).first()
    if not stats:
        return {}

    return {
        # Overall
        'user_level': stats.overall_level,
        'xp': stats.overall_xp,
        'next_level_xp': stats.overall_next_level_xp,
        'xp_to_next': stats.overall_xp_to_next_level,
        'progress_percent': stats.overall_progress_percent,

        # Chore
        'chore_xp': stats.chore_xp,
        'chore_level': stats.chore_level,
        'chore_next_level_xp': stats.chore_next_level_xp,
        'chore_xp_to_next': stats.chore_xp_to_next_level,
        'chore_progress_percent': stats.chore_progress_percent,

        # Reading
        'reading_xp': stats.reading_xp,
        'reading_level': stats.reading_level,
        'reading_next_level_xp': stats.reading_next_level_xp,
        'reading_xp_to_next': stats.reading_xp_to_next_level,
        'reading_progress_percent': stats.reading_progress_percent,
    }

def user_profile_picture(request):
    if request.user.is_authenticated:
        try:
            stats = UserStats.objects.get(user=request.user)
            return {'profile_picture_url': stats.profile_picture.url if stats.profile_picture else None}
        except UserStats.DoesNotExist:
            pass
    return {'profile_picture_url': None}