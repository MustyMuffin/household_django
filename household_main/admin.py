from django.contrib import admin

from .models import Note, Entry

admin.site.register(Note)
admin.site.register(Entry)