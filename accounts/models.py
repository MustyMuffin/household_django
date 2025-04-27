from django.db import models
from django.contrib.auth.models import User
import math

class XPSettings(models.Model):
    base = models.PositiveIntegerField(default=50)
    exponent = models.FloatField(default=0.75)

    def save(self, *args, **kwargs):
        if not self.pk and XPSettings.objects.exists():
            raise Exception('There can only be one XPSettings instance')
        return super().save(*args, **kwargs)

    def __str__(self):
        return "XP Settings"

    class Meta:
        verbose_name_plural = "XP Settings"

class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    last_updated = models.DateTimeField(auto_now=True)

    def update_level(self):
        try:
            settings_instance = XPSettings.objects.first()
            base = settings_instance.base
            exponent = settings_instance.exponent
        except AttributeError:
            base = 50
            exponent = 0.75

        if self.xp == 0:
            self.level = 1
        else:
            self.level = max(1, int((self.xp / base) ** exponent))
        self.save()

    def next_level_xp(self):
        return int(((self.level + 1) ** (1 / XPSettings.exponent)) * XPSettings.base)

    def current_level_xp(self):
        return int((self.level ** (1 / XPSettings.exponent)) * XPSettings.base)

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
