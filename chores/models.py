from django.db import models
from django.contrib.auth.models import User


class Chores(models.Model):
    """Table mapping admin selected chores to variables"""
    text = models.CharField(max_length=200)
    price = models.IntegerField()

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


class ChoreEntry(models.Model):
    """For logging the labor"""
    chore_entry = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'chore_entries'

    def __str__(self):
        """Return a simple string representing the entry."""
        return f"{self.text[:50]}..."