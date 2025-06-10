from django.contrib import admin

from .models import Book, BookEntry, BooksRead, BookCategory, BookSeries

admin.site.register(BookCategory)
admin.site.register(Book)
admin.site.register(BookEntry)
admin.site.register(BooksRead)
admin.site.register(BookSeries)