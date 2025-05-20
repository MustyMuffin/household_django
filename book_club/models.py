from django.db import models
from django.contrib.auth.models import User

class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'book_categories'

    def __str__(self):
        return self.name

class Book(models.Model):
    """A book the user is logging."""
    text = models.CharField(max_length=100)
    words = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    book_category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text

class BookEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'book_entries'

class BooksRead(models.Model):
    """For tracking books read"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_name = models.CharField(max_length=20, default="BoomWhacker")
    date_added = models.DateTimeField(auto_now_add=True)

class BookProgressTracker(models.Model):
    """For tracking book progress and awarding xp for books still in progress."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_name = models.ForeignKey(Book, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    words_completed = models.IntegerField(default=0)
    text = models.CharField(max_length=100, default="Chapter 1")