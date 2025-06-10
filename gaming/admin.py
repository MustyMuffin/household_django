from django.contrib import admin

from .models import Game, GameEntry, GamesBeaten, GameCategory, GameLink

admin.site.register(GameCategory)
admin.site.register(Game)
admin.site.register(GameEntry)
admin.site.register(GamesBeaten)
admin.site.register(GameLink)