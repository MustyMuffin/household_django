from decimal import Decimal
from accounts.models import XPLog, XPSettings, UserStats
from accounts.xp_utils import XPManager

def award_xp(user, source_object=None, reason="", source_type="chore"):
    """Award XP to a user based on the source object (chore or book)."""

    # Always ensure they have a UserStats profile
    userstats, created = UserStats.objects.get_or_create(user=user)

    # Before awarding, record old level
    old_level = XPManager.level_from_xp(userstats.xp)

    # Determine how much XP to award
    xp_awarded = 0

    xp_settings = XPSettings.objects.first()
    if not xp_settings:
        xp_settings = XPSettings(base=50, exponent=0.75)  # fallback settings

    if source_type == "chore":
        # We expect chore.wage
        xp_awarded = int(Decimal(source_object.wage) * xp_settings.xp_per_chore_wage)
    elif source_type == "book":
        # We expect book.words
        xp_awarded = int(Decimal(source_object.words) * xp_settings.xp_per_word)
    else:
        xp_awarded = 0  # fallback if something weird

    # Add XP to user's profile
    userstats.xp += xp_awarded
    userstats.save(update_fields=["xp"])

    # Log the XP gain
    XPLog.objects.create(user=user, amount=xp_awarded, reason=reason)

    # Check new level
    new_level = XPManager.level_from_xp(userstats.xp)

    # Return useful data
    return {
        "xp_awarded": xp_awarded,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
    }
