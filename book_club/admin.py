from django.contrib import admin

from .models import Book, BookEntry, BooksRead, WordsRead, BookCategory

admin.site.register(BookCategory)
admin.site.register(Book)
admin.site.register(BookEntry)
admin.site.register(BooksRead)
admin.site.register(WordsRead)