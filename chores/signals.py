from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChoreEntry, Chore
from accounts.models import UserStats, XPLog


@receiver(post_save, sender=ChoreEntry)
def award_chore_xp(sender, instance, created, **kwargs):
    if created:
        profile, _ = UserStats.objects.get_or_create(user=instance.user)
        wage = float(instance.wage)
        xp_amount = int(wage * 10)  # Adjust scale as needed
        profile.xp += xp_amount
        profile.save()

        XPLog.objects.create(
            user=instance.user,
            amount=xp_amount,
            reason=f"Completed chore: {instance.chore.text}"
        )

        profile.update_level()