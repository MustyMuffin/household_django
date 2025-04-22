from django.db import models
from django.contrib.auth.models import User
import math


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - XP: {self.xp}"

    def update_level(self):
        new_level = math.floor((self.xp / 50) ** 0.75)
        if new_level < 1:
            new_level = 1
        if new_level != self.level:
            self.level = new_level
            self.save()

    def next_level_xp(self):
        return int(((self.level + 1) ** (1 / 0.75)) * 50)

    def current_level_xp(self):
        return int((self.level ** (1 / 0.75)) * 50)

    def progress_percent(self):
        current = self.current_level_xp()
        next = self.next_level_xp()
        return int(((self.xp - current) / (next - current)) * 100)

class XPLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: +{self.amount} XP for {self.reason} on {self.date_awarded.strftime('%Y-%m-%d %H:%M')}"
