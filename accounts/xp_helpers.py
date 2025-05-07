from decimal import Decimal
from accounts.models import XPLog, XPSettings, UserStats
from accounts.xp_utils import XPManager

def award_xp(user, source_object=None, reason="", source_type="chore"):
    """Award XP to a user based on the source object (chore or book)."""

    userstats, created = UserStats.objects.get_or_create(user=user)

    old_level = XPManager.level_from_xp(userstats.xp)

    xp_awarded = 0

    xp_settings = XPSettings.objects.first()
    if not xp_settings:
        xp_settings = XPSettings(base=50, exponent=0.75)
        """ fallback settings are 50 for base and 0.75 xp curve
        admin should dial in curve and base in admin panel """

    if source_type == "chore":
        xp_awarded = int(Decimal(source_object.wage) * xp_settings.xp_per_chore_wage)
    elif source_type == "book":
        xp_awarded = int(Decimal(source_object.words) * xp_settings.xp_per_word)
    elif source_type == "book_partial":
        xp_awarded = int(source_object * xp_settings.xp_per_word)
    else:
        xp_awarded = 0

    userstats.xp += xp_awarded
    userstats.save(update_fields=["xp"])

    XPLog.objects.create(user=user, amount=xp_awarded, reason=reason)

    new_level = XPManager.level_from_xp(userstats.xp)

    return {
        "xp_awarded": xp_awarded,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
    }
