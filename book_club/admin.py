from django.contrib import admin

from .models import Book, BookEntry, BooksRead, BookCategory

admin.site.register(BookCategory)
admin.site.register(Book)
admin.site.register(BookEntry)
admin.site.register(BooksRead)