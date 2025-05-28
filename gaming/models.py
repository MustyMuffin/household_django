from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField

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

    def __str__(self):
        """Return a string representation of the model."""
        return self.name

class GameProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="game_progress")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="progress_logs")
    hours_played = models.DecimalField(max_digits=5, decimal_places=2)
    beaten = models.BooleanField(default=False)
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

# class GameProgressTracker(models.Model):
#     """For tracking game progress and awarding xp for games still in progress."""
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     game_name = models.ForeignKey(Game, on_delete=models.CASCADE)
#     date_added = models.DateTimeField(auto_now_add=True)
#     hours_completed = models.IntegerField(default=0)
#     text = models.CharField(max_length=100, default="Chapter 1")

class RetroGameCache(models.Model):
    retro_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    console = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    data = models.JSONField()
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


