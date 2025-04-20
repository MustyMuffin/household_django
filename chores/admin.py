from django.contrib import admin

from .models import Chore, EarnedWage, ChoreCategory, ChoreEntry

admin.site.register(Chore)
admin.site.register(ChoreEntry)
admin.site.register(EarnedWage)
admin.site.register(ChoreCategory)
