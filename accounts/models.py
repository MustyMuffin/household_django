from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from accounts.xp_utils import XPManager


class XPSettings(models.Model):
    base = models.PositiveIntegerField(default=50)
    exponent = models.FloatField(default=0.75)

    def __str__(self):
        return f"XP Settings (Base: {self.base}, Exponent: {self.exponent})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # First save normally

        # 1. Clear cached settings
        XPManager.clear_cache()

        # 2. Update all UserStats based on new XP curve
        for stats in UserStats.objects.all():
            xp = stats.xp
            new_level = XPManager.level_from_xp(xp)
            stats.level = new_level
            stats.save(update_fields=["level"])  # only save the level field for efficiency

    class Meta:
        verbose_name_plural = 'XP Settings'

class UserStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    def update_level(self):
        from accounts.xp_utils import XPManager
        self.level = XPManager.level_from_xp(self.xp)
        self.save(update_fields=["level"])  # only save "level" field for efficiency


class XPLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: +{self.amount} XP for {self.reason} on {self.date_awarded.strftime('%Y-%m-%d %H:%M')}"
