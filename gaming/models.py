from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField
from django.conf import settings

class GameCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'game_categories'

    def __str__(self):
        return self.name

class Game(models.Model):
    """A game the user is logging."""
    name = models.CharField(max_length=100)
    image_url = models.ImageField(upload_to='images/', null=True, blank=True)
    hours_main_story = models.IntegerField(default=0)
    hours_main_extra = models.IntegerField(default=0)
    hours_completionist = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    game_category = models.ForeignKey(GameCategory, on_delete=models.SET_NULL, null=True, blank=True)
    achievements_url = models.URLField(blank=True, null=True)
    retro_game = models.ForeignKey("RetroGameEntry", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name

class GameProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="game_progress")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="progress_logs")
    hours_played = models.DecimalField(max_digits=5, decimal_places=2)
    beaten = models.BooleanField(default=False)
    mastered = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_at"]
        unique_together = ("user", "game", "logged_at")

    def __str__(self):
        return f"{self.user.username} - {self.game.name} - {self.hours_played}h{' ✅' if self.beaten else ''}"

class GameEntry(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'game_entries'

class GamesBeaten(models.Model):
    """For tracking games played"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_name = models.CharField(max_length=20, default="Doom")
    date_added = models.DateTimeField(auto_now_add=True)

class CollectibleType(models.Model):
    """Defines a collectible type per game (e.g., 'Moons', 'Korok Seeds')."""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='collectible_types')
    name = models.CharField(max_length=100)
    total_available = models.PositiveIntegerField(help_text="Total available in the game")

    def __str__(self):
        return f"{self.name} ({self.game.name})"


class UserCollectibleProgress(models.Model):
    """Tracks how many of each collectible type a user has found."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collectible_type = models.ForeignKey(CollectibleType, on_delete=models.CASCADE)
    collected = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'collectible_type')

class RetroGameCache(models.Model):
    retro_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    console = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    data = models.JSONField()
    achievements = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.console})"

class TrueAchievementsGameCache(models.Model):
    ta_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True)
    data = models.JSONField()  # Store full scraped data blob (e.g. achievements)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.platform})"

class IGDBGameCache(models.Model):
    igdb_id = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    data = models.JSONField()

class GameLink(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="links")
    platform = models.CharField(max_length=50)
    url = models.URLField()

class RetroConsole(models.Model):
    console_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} (ID: {self.console_id})"

class RetroGameEntry(models.Model):
    retro_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    console_id = models.IntegerField()
    console_name = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.console_name})"


class UserGameAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    game_progress = models.ForeignKey(GameProgress, on_delete=models.CASCADE)

    retro_id = models.IntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    points = models.IntegerField(default=0)
    unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "game", "retro_id", "title")
        verbose_name = "Game Achievement"
        verbose_name_plural = "Game Achievements"
        indexes = [
            models.Index(fields=["user", "game"]),
            models.Index(fields=["retro_id"]),
            models.Index(fields=["unlocked"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.game.name})"


