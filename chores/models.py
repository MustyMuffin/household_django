from django.db import models


class Chores(models.Model):
    """Table mapping user selected chores to variables"""
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text


class ChoreEntry(models.Model):
    """For logging the labor"""
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    chore_entry = models.ForeignKey(Chores, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'chore_entries'