from django.urls import path, include
from .views import (games_by_category, games, game,
                    game_backlog, new_game_entry, new_game_tracker_entry,
                    update_game_tracker_entry, achievements_view, add_new_game,
                    )

app_name = "gaming"
urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', games_by_category, name='games_by_category'),
    path('games/', games, name='games'),
    path('games/<int:game_id>/', game, name='game'),
    path('game_backlog/', game_backlog, name='game_backlog'),
    path('new_game_entry/<int:game_id>/', new_game_entry, name='new_game_entry'),
    path('new_game_tracker_entry/<int:game_id>/', new_game_tracker_entry, name='new_game_tracker_entry'),
    path('update_game_tracker_entry/<int:pk>/', update_game_tracker_entry, name='update_game_tracker_entry'),
    path('achievements/', achievements_view, name='achievements'),
    # Add new game (Privileged users only)
    path('add_new_game/', add_new_game, name='add_new_game'),
]