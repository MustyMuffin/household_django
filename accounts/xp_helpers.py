from decimal import Decimal

from django.urls import reverse

from .models import XPLog, XPSettings, UserStats
from scheduling.models import Notification

from .xp_utils import XPManager

def award_xp(user, source_object=None, reason="", source_type="chore", override_xp_amount=None, request=None):
    """Award XP to a user based on the source object, or override with a specific XP amount."""

    userstats, _ = UserStats.objects.get_or_create(user=user)

    old_level = userstats.overall_level
    old_level_chores = userstats.chore_level
    old_level_reading = userstats.reading_level
    old_level_gaming = userstats.gaming_level

    xp_settings = XPSettings.objects.first() or XPSettings(base=100, exponent=1.25)

    xp_awarded = int(override_xp_amount) if override_xp_amount is not None else 0

    if override_xp_amount is None:
        if source_type == "chore" and source_object:
            xp_awarded = int(Decimal(source_object.wage) * xp_settings.xp_per_chore_wage)
            userstats.chore_xp += xp_awarded

        elif source_type == "book" and source_object:
            xp_awarded = int(Decimal(source_object.words) * xp_settings.xp_per_word)
            userstats.reading_xp += xp_awarded

        elif source_type == "book_partial" and source_object:
            xp_awarded = int(Decimal(source_object) * xp_settings.xp_per_word)
            userstats.reading_xp += xp_awarded

        elif source_type == "game_partial" and source_object:
            try:
                hours_played = Decimal(source_object)
                print("DEBUG:hours_played = ", hours_played)
                xp_awarded = int(hours_played * xp_settings.xp_per_hour_gamed) if hours_played > 0 else 0
                print("DEBUG xp_awarded = ", xp_awarded)

                userstats.gaming_xp += xp_awarded
            except (TypeError, ValueError, InvalidOperation):
                print("EXCEPT DEBUG xp_awarded = ", xp_awarded)
                xp_awarded = 0

        elif source_type == "finished_book":
            xp_awarded = xp_settings.xp_per_book
            userstats.reading_xp += xp_awarded

        elif source_type == "finished_game":
            xp_awarded = xp_settings.xp_per_game_beaten
            userstats.gaming_xp += xp_awarded

    userstats.overall_xp += xp_awarded

    userstats.save(update_fields=["overall_xp", "chore_xp", "reading_xp", "gaming_xp"])

    userstats.update_levels()

    new_level = userstats.overall_level
    new_level_chores = userstats.chore_level
    new_level_reading = userstats.reading_level
    new_level_gaming = userstats.gaming_level

    if request:
        from django.contrib import messages

        if new_level > old_level:
            messages.success(request, f"🎉 You leveled up to Level {new_level}!")
            Notification.objects.create(
                user=user,
                message=f"🎉 Level up! You’ve reached level {new_level}.",
                url=reverse('accounts:user_profile', args=[user.username])
            )
        if new_level_chores > old_level_chores:
            messages.success(request, f"🧹 You reached Chore Level {new_level_chores}!")
            Notification.objects.create(
                user=user,
                message=f"🎉 Level up! 🧹 You reached Chore Level {new_level_chores}.",
                url=reverse('accounts:user_profile', args=[user.username])
            )
        if new_level_reading > old_level_reading:
            messages.success(request, f"📚 You reached Reading Level {new_level_reading}!")
            Notification.objects.create(
                user=user,
                message=f"🎉 Level up! 📚 You reached Reading Level {new_level_reading}.",
                url=reverse('accounts:user_profile', args=[user.username])
            )

        if new_level_gaming > old_level_gaming:
            messages.success(request, f"🎮 You reached Gaming Level {new_level_gaming}!")
            Notification.objects.create(
                user=user,
                message=f"🎉 Level up! 🎮 You reached Gaming Level {new_level_gaming}.",
                url=reverse('accounts:user_profile', args=[user.username])
            )

    XPLog.objects.create(user=user, amount=xp_awarded, reason=reason)

    return {
        "xp_awarded": xp_awarded,
        "old_level": old_level,
        "new_level": userstats.overall_level,
        "leveled_up": userstats.overall_level > old_level,
        "old_level_chores": old_level_chores,
        "new_level_chores": userstats.chore_level,
        "chores_leveled_up": userstats.chore_level > old_level_chores,
        "old_level_reading": old_level_reading,
        "new_level_reading": userstats.reading_level,
        "reading_leveled_up": userstats.reading_level > old_level_reading,
        "gaming_leveled_up": userstats.gaming_level > old_level_gaming,
    }
