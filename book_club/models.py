from django.db import models
from django.contrib.auth.models import User

class BookSeries(models.Model):
    series_name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'series'

    def __str__(self):
        return self.series_name

class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'book_categories'

    def __str__(self):
        return self.name

class Book(models.Model):
    """A book the user is logging."""
    title = models.CharField(max_length=100)
    words = models.IntegerField(null=True, blank=True, default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    book_category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, blank=True)
    pages = models.IntegerField(null=True, blank=True, default=0)
    series = models.ForeignKey(BookSeries, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title

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
    book_name = models.ForeignKey(Book, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book_name')

class BookProgressTracker(models.Model):
    """For tracking book progress and awarding xp for books still in progress."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_name = models.ForeignKey(Book, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    words_completed = models.IntegerField(default=0)
    text = models.CharField(max_length=100, default="Chapter 1")
    want_to_read = models.BooleanField(default=False)

class BookMetadata(models.Model):
    book = models.OneToOneField('Book', on_delete=models.CASCADE, related_name='metadata')
    source = models.CharField(max_length=50)
    title = models.CharField(max_length=255, blank=True)
    authors = models.JSONField(blank=True, default=list)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=1000, null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    pages = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return f"Metadata for {self.book.title} from {self.source}"