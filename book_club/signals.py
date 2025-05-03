# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import BookEntry
# from accounts.models import UserStats, XPLog
#
#
# # @receiver(post_save, sender=BookEntry)
# # def award_book_xp(sender, instance, created, **kwargs):
# #     if created:
# #         profile, _ = UserStats.objects.get_or_create(user=instance.user)
# #         word_count = instance.book.words
# #         xp_amount = int(word_count * 0.002)  # A 100,000-word book = 200 XP at a 0.002 scale factor.
# #         profile.xp += xp_amount
# #         profile.save()
# #
# #         XPLog.objects.create(
# #             user=instance.user,
# #             amount=xp_amount,
# #             reason=f"Completed book: {instance.book.text}"
# #         )
# #
# #         profile.update_level()