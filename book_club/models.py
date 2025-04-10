from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    """A book the user is logging."""
    text = models.CharField(max_length=20)
    pages = models.DecimalField(max_digits=6, decimal_places=0)
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