from decimal import Decimal
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.apps import apps
from .constants import ALLOWED_APPS
from .badge_helpers import BadgeProgressProvider


class XPSettings(models.Model):
    base = models.PositiveIntegerField(default=100)
    exponent = models.FloatField(default=1.25)
    chore_base = models.PositiveIntegerField(default=100)
    chore_exponent = models.FloatField(default=1.25)
    reading_base = models.PositiveIntegerField(default=100)
    reading_exponent = models.FloatField(default=1.25)
    xp_per_word = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.002'))
    xp_per_chore_wage = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('10.0'))
    xp_per_book = models.IntegerField(default='50')
    locked = models.BooleanField(default=False)

    def __str__(self):
        return f"XP Settings (Base: {self.base}, Exponent: {self.exponent})"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_settings = XPSettings.objects.get(pk=self.pk) if not is_new else None

        base_changed = exponent_changed = chore_changed = reading_changed = True

        if old_settings:
            base_changed = self.base != old_settings.base
            exponent_changed = self.exponent != old_settings.exponent
            chore_changed = self.chore_base != old_settings.chore_base or self.chore_exponent != old_settings.chore_exponent
            reading_changed = self.reading_base != old_settings.reading_base or self.reading_exponent != old_settings.reading_exponent

        super().save(*args, **kwargs)

        from .xp_utils import XPManager
        XPManager.clear_cache()

        if base_changed or exponent_changed:
            XPTable.objects.all().delete()
            XPTable.objects.bulk_create([
                XPTable(overall_level=level, xp_required=int(self.base * (level ** self.exponent)))
                for level in range(1, 101)
            ])

        if chore_changed:
            ChoreXPTable.objects.all().delete()
            ChoreXPTable.objects.bulk_create([
                ChoreXPTable(chore_level=level, chore_xp_required=int(self.chore_base * (level ** self.chore_exponent)))
                for level in range(1, 101)
            ])

        if reading_changed:
            ReadingXPTable.objects.all().delete()
            ReadingXPTable.objects.bulk_create([
                ReadingXPTable(reading_level=level, reading_xp_required=int(self.reading_base * (level ** self.reading_exponent)))
                for level in range(1, 101)
            ])

        if base_changed or chore_changed or reading_changed:
            XPManager.resync_all_user_levels()

    @classmethod
    def get_settings(cls):
        settings_obj = cls.objects.first()
        if not settings_obj:
            return cls(
                base=100, exponent=1.25,
                chore_base=100, chore_exponent=1.25,
                reading_base=100, reading_exponent=1.25,
                xp_per_word=0.0, xp_per_chore_wage=0.0
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

    overall_xp = models.PositiveIntegerField(default=0)
    chore_xp = models.PositiveIntegerField(default=0)
    reading_xp = models.PositiveIntegerField(default=0)
    words_read = models.PositiveIntegerField(default=0)

    overall_level = models.PositiveIntegerField(default=1)
    chore_level = models.PositiveIntegerField(default=1)
    reading_level = models.PositiveIntegerField(default=1)

    def update_levels(self):
        """Updates stored level fields based on XP."""
        from accounts.xp_utils import XPManager

        self.overall_level = XPManager.level_info(self.overall_xp, kind="overall").get("level", 1)
        self.chore_level = XPManager.level_info(self.chore_xp, kind="chore").get("level", 1)
        self.reading_level = XPManager.level_info(self.reading_xp, kind="reading").get("level", 1)
        self.save(update_fields=["overall_level", "chore_level", "reading_level"])

    def _get_xp_data(self, xp_value, table_model, level_field, xp_field):
        """Returns dict of XP metadata for a given table and XP value."""
        level_entry = table_model.objects.filter(
            **{f"{xp_field}__lte": xp_value}
        ).order_by(f"-{level_field}").first()

        level = getattr(level_entry, level_field, 1) if level_entry else 1
        current_xp = getattr(level_entry, xp_field, 0) if level_entry else 0

        next_entry = table_model.objects.filter(**{level_field: level + 1}).first()
        next_xp = getattr(next_entry, xp_field, current_xp) if next_entry else current_xp

        percent = 100 if next_xp == current_xp else round((xp_value - current_xp) / (next_xp - current_xp) * 100, 2)

        return {
            "level": level,
            "current_xp": current_xp,
            "next_xp": next_xp,
            "percent": percent,
            "to_next": max(0, next_xp - xp_value),
        }

    # --- Overall XP ---
    @property
    def overall_level_data(self):
        return self._get_xp_data(self.overall_xp, XPTable, 'overall_level', 'xp_required')

    @property
    def overall_current_level_xp(self):
        return self.overall_level_data["current_xp"]

    @property
    def overall_next_level_xp(self):
        return self.overall_level_data["next_xp"]

    @property
    def overall_progress_percent(self):
        return self.overall_level_data["percent"]

    @property
    def overall_xp_to_next_level(self):
        return self.overall_level_data["to_next"]

    # --- Chore XP ---
    @property
    def chore_level_data(self):
        return self._get_xp_data(self.chore_xp, ChoreXPTable, 'chore_level', 'chore_xp_required')

    @property
    def chore_current_level_xp(self):
        return self.chore_level_data["current_xp"]

    @property
    def chore_next_level_xp(self):
        return self.chore_level_data["next_xp"]

    @property
    def chore_progress_percent(self):
        return self.chore_level_data["percent"]

    @property
    def chore_xp_to_next_level(self):
        return self.chore_level_data["to_next"]

    # --- Reading XP ---
    @property
    def reading_level_data(self):
        return self._get_xp_data(self.reading_xp, ReadingXPTable, 'reading_level', 'reading_xp_required')

    @property
    def reading_current_level_xp(self):
        return self.reading_level_data["current_xp"]

    @property
    def reading_next_level_xp(self):
        return self.reading_level_data["next_xp"]

    @property
    def reading_progress_percent(self):
        return self.reading_level_data["percent"]

    @property
    def reading_xp_to_next_level(self):
        return self.reading_level_data["to_next"]


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

    def get_progress_for_user(self, user, return_raw=False):
        value = BadgeProgressProvider.get_progress(self, user)
        if return_raw:
            return value
        if not self.milestone_value:
            return 0
        return min(100, round((value / self.milestone_value) * 100))

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

class XPTable(models.Model):
    overall_level = models.PositiveIntegerField(unique=True)
    xp_required = models.PositiveIntegerField()

    class Meta:
        ordering = ['overall_level']

    def __str__(self):
        return f"Level {self.overall_level} – {self.xp_required} XP"

class ChoreXPTable(models.Model):
    chore_level = models.PositiveIntegerField(unique=True)
    chore_xp_required = models.PositiveIntegerField()

    class Meta:
        ordering = ['chore_level']

    def __str__(self):
        return f"Chore Level = {self.chore_level} – {self.chore_xp_required} XP"

class ReadingXPTable(models.Model):
    reading_level = models.PositiveIntegerField(unique=True)
    reading_xp_required = models.PositiveIntegerField()

    class Meta:
        ordering = ['reading_level']

    def __str__(self):
        return f"Reading Level = {self.reading_level} – {self.reading_xp_required} XP"
