from django.urls import path, include
from .views import (
    games_by_category, games, game_detail,
    game_backlog, add_new_game,
    achievements_view, fetch_game_data_api,
    log_game_progress
    )

app_name = "gaming"

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', games_by_category, name='games_by_category'),
    path('games/', games, name='games'),
    path("game/<int:game_id>/", game_detail, name="game_detail"),
    path('game_backlog/', game_backlog, name='game_backlog'),

    path('log_game_progress/<int:game_id>/', log_game_progress, name='log_game_progress'),

    path('achievements/', achievements_view, name='achievements'),
    path('add_new_game/', add_new_game, name='add_new_game'),

    # 🔌 API Endpoints
    path('api/fetch_game_data/', fetch_game_data_api, name='fetch_game_data_api'),
]