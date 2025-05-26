from django.contrib import admin

from .models import Game, GameEntry, GamesPlayed, GameCategory

admin.site.register(GameCategory)
admin.site.register(Game)
admin.site.register(GameEntry)
admin.site.register(GamesPlayed)