from django.contrib import admin

from .models import Book, BookEntry

admin.site.register(Book)
admin.site.register(BookEntry)