from django.contrib import admin

from .models import Book, BookEntry, BooksRead, WordsRead

admin.site.register(Book)
admin.site.register(BookEntry)
admin.site.register(BooksRead)
admin.site.register(WordsRead)