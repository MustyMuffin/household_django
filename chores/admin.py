from django.contrib import admin

from .models import Chores
from .models import ChoreEntry

admin.site.register(Chores)
admin.site.register(ChoreEntry)
