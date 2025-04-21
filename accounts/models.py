from django.db import models
# from django.contrib.auth.models import User
# from chores.models import ChoreEntry  # or Chore, etc.
#
# class UserStats(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     earnedLifetime = models.PositiveIntegerField(default=0)
#
#     def update_total(self):
#         self.earnedLifetime = ChoreEntry.objects.filter(user=self.user).count()
#         self.save()