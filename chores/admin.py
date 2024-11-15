from django.contrib import admin

from .models import Chore
from .models import ChoreEntry

admin.site.register(Chore)
admin.site.register(ChoreEntry)
