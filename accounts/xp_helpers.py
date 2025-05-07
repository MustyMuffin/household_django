from decimal import Decimal
from accounts.models import XPLog, XPSettings, UserStats
from accounts.xp_utils import XPManager

def award_xp(user, source_object=None, reason="", source_type="chore", override_xp_amount=None):
    """Award XP to a user based on the source object, or override with a specific XP amount."""

    userstats, created = UserStats.objects.get_or_create(user=user)
    old_level = XPManager.level_from_xp(userstats.xp)

    # Fetch XP settings (or fallback)
    xp_settings = XPSettings.objects.first()
    if not xp_settings:
        xp_settings = XPSettings(base=50, exponent=0.75)

    if override_xp_amount is not None:
        xp_awarded = int(override_xp_amount)
    else:
        if source_type == "chore":
            xp_awarded = int(Decimal(source_object.wage) * xp_settings.xp_per_chore_wage)
        elif source_type == "book":
            xp_awarded = int(Decimal(source_object.words) * xp_settings.xp_per_word)
        elif source_type == "book_partial":
            xp_awarded = int(Decimal(source_object) * xp_settings.xp_per_word)
        elif source_type == "finished_book":
            xp_awarded = xp_settings.xp_per_book
        else:
            xp_awarded = 0

    # Update stats
    userstats.xp += xp_awarded
    userstats.save(update_fields=["xp"])

    # Log XP gain
    XPLog.objects.create(user=user, amount=xp_awarded, reason=reason)

    new_level = XPManager.level_from_xp(userstats.xp)

    return {
        "xp_awarded": xp_awarded,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
    }
