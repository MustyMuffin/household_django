from django.db import models
from django.contrib.auth.models import User
import math

class XPSettings(models.Model):
    base = models.PositiveIntegerField(default=50)
    exponent = models.FloatField(default=0.75)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

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
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    def update_level(self):
        settings_instance = XPSettings.load()
        base = settings_instance.base
        exponent = settings_instance.exponent

        leveled_up = False

        while True:
            next_level = self.level + 1
            next_level_xp = int(base * (next_level ** exponent))
            if self.xp >= next_level_xp:
                self.level += 1
                leveled_up = True
            else:
                break

        if leveled_up:
            self.save()

    # def update_level(self):
    #     try:
    #         settings_instance = XPSettings.load()
    #         base = settings_instance.base
    #         exponent = settings_instance.exponent
    #     except (AttributeError, XPSettings.DoesNotExist):
    #         base = 50
    #         exponent = 0.75
    #
    #     if self.xp <= 0:
    #         self.level = 1
    #     else:
    #         # Solve for level based on inverse curve: level = (xp / base) ** (1/exponent)
    #         self.level = max(1, int((self.xp / base) ** (1 / exponent)))
    #
    #     self.save()

    def next_level_xp(self):
        try:
            settings_instance = XPSettings.load()
            base = settings_instance.base
            exponent = settings_instance.exponent
        except (AttributeError, XPSettings.DoesNotExist):
            base = 50
            exponent = 0.75

        next_level = self.level + 1
        required_xp = int(base * (next_level ** exponent))
        return required_xp

    def current_level_xp(self):
        try:
            settings_instance = XPSettings.load()
            base = settings_instance.base
            exponent = settings_instance.exponent
        except (AttributeError, XPSettings.DoesNotExist):
            base = 50
            exponent = 0.75

        current_xp = int(base * (self.level ** exponent))
        return current_xp

    def progress_percent(self):
        next_xp = self.next_level_xp()
        current_xp = self.current_level_xp()
        if next_xp == current_xp:
            return 0  # Avoid divide-by-zero if something weird happens

        progress = (self.xp - current_xp) / (next_xp - current_xp) * 100
        return max(0, min(int(progress), 100))  # clamp between 0-100


class XPLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: +{self.amount} XP for {self.reason} on {self.date_awarded.strftime('%Y-%m-%d %H:%M')}"
