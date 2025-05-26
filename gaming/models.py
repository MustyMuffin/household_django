from django.db import models
from django.contrib.auth.models import User

class GameCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'game_categories'

    def __str__(self):
        return self.name

class Game(models.Model):
    """A game the user is logging."""
    name = models.CharField(max_length=100)
    hours = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    game_category = models.ForeignKey(GameCategory, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name

class GameEntry(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'game_entries'

class GamesPlayed(models.Model):
    """For tracking games played"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_name = models.CharField(max_length=20, default="Doom")
    date_added = models.DateTimeField(auto_now_add=True)

class GameProgressTracker(models.Model):
    """For tracking game progress and awarding xp for games still in progress."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_name = models.ForeignKey(Game, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    hours_completed = models.IntegerField(default=0)
    text = models.CharField(max_length=100, default="Chapter 1")
