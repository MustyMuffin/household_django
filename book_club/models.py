from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    """A book the user is logging."""
    text = models.CharField(max_length=20)
    words = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text

class BookEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'book_entries'

class WordsRead(models.Model):
    """For tracking the pages read"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    wordsLifetime = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

class BooksRead(models.Model):
    """For tracking books read"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_name = models.CharField(max_length=20, default="BoomWhacker")
    date_added = models.DateTimeField(auto_now_add=True)

# class BookProgressTracker(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     book = models.ForeignKey(Book, on_delete=models.CASCADE)
#     pagesLifetime = models.IntegerField(default=0)