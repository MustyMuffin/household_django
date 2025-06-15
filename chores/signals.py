# from datetime import time
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.http import request
#
# from accounts.badge_helpers import check_and_award_badges
# from chores.models import ChoreEntry
# from accounts.models import Badge, UserBadge
# from django.contrib.contenttypes.models import ContentType
#
#
# @receiver(post_save, sender=ChoreEntry)
# def check_chore_badges(sender, instance, created, **kwargs):
#     if not created:
#         return
#
#     user = instance.user
#     chore = instance.chore
#
#     # Get all badges for the "chores" app that match this specific chore milestone
#     badges = Badge.objects.filter(
#         app_label="chores",
#         milestone_type=str(chore.name)
#     )
#
#     for badge in badges:
#         completed_count = ChoreEntry.objects.filter(user=user, chore=chore).count()
#         if completed_count >= badge.milestone_value:
#             UserBadge.objects.get_or_create(user=user, badge=badge)