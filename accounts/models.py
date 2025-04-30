from decimal import Decimal
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from accounts.xp_utils import XPManager
from django.apps import apps
from .constants import ALLOWED_APPS

class XPSettings(models.Model):
    base = models.PositiveIntegerField(default=50)
    exponent = models.FloatField(default=0.75)
    xp_per_word = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.002'))
    xp_per_chore_wage = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('10.0'))

    def __str__(self):
        return f"XP Settings (Base: {self.base}, Exponent: {self.exponent})"

    def save(self, *args, **kwargs):
        is_new = not self.pk

        if is_new and XPSettings.objects.exists():
            XPSettings.objects.all().delete()

        if not is_new:
            old_settings = XPSettings.objects.get(pk=self.pk)
            base_changed = self.base != old_settings.base
            exponent_changed = self.exponent != old_settings.exponent
        else:
            base_changed = exponent_changed = True

        super().save(*args, **kwargs)

        from accounts.xp_utils import XPManager
        XPManager.clear_cache()

        if base_changed or exponent_changed:
            XPManager.resync_all_user_levels()

    @classmethod
    def get_settings(cls):
        try:
            settings_obj = XPSettings.objects.first()
            if not settings_obj:
                raise XPSettings.DoesNotExist
        except XPSettings.DoesNotExist:
            settings_obj = cls(
                base=50,
                exponent=0.75,
                xp_per_word=0.0,
                xp_per_chore_wage=0.0,
            )
        return settings_obj

    @classmethod
    def get_xp_per_word(cls):
        if apps.is_installed('book_club'):
            return cls.get_settings().xp_per_word
        return 0.0

    @classmethod
    def get_xp_per_chore_wage(cls):
        if apps.is_installed('chores'):
            return cls.get_settings().xp_per_chore_wage
        return 0.0

    class Meta:
        verbose_name_plural = 'XP Settings'

class UserStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    words_read = models.IntegerField(default=0)

    @property
    def level(self):
        from accounts.xp_utils import XPManager
        return XPManager.level_from_xp(self.xp)

    @property
    def next_level_xp(self):
        from accounts.xp_utils import XPManager
        return XPManager.next_level_xp(self.level)

    @property
    def current_level_xp(self):
        from accounts.xp_utils import XPManager
        return XPManager.xp_for_level(self.level)

    @property
    def progress_percent(self):
        from accounts.xp_utils import XPManager
        return XPManager.progress_percent(self.xp, self.level)

    @property
    def xp_to_next_level(self):
        from accounts.xp_utils import XPManager
        return XPManager.xp_to_next_level(self.xp, self.level)

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='household/badges/')
    app_label = models.CharField(
        max_length=50,
        choices=ALLOWED_APPS,
        help_text="Select the app/module this badge applies to."
    )
    milestone_type = models.CharField(max_length=100)
    milestone_value = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

class XPLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: +{self.amount} XP for {self.reason} on {self.date_awarded.strftime('%Y-%m-%d %H:%M')}"
