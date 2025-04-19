# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import ChoreEntry, EarnedWage
#
# @receiver(post_save, sender=ChoreEntry)
# def update_earned_lifetime(sender, instance, created, **kwargs):
#     if created:
#         profile, _ = ChoreEntry.objects.get(user_id=instance.user)
#         profile.earnedLifetime += instance.wage
#         profile.save()