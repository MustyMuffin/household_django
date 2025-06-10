from django.urls import path, include
from .views import (
    games_by_category, games, game_detail,
    game_backlog, add_new_game,
    achievements_view, fetch_game_data_api,
    log_game_progress, unpair_retro_game,
    generate_game_links, retro_pairing,
    add_link_source, remove_game_link
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

    path("games/<int:game_id>/generate_links/", generate_game_links, name="generate_game_links"),

    path("games/<int:game_id>/retro_pairing/", retro_pairing, name="retro_pairing"),

    path("games/<int:game_id>/unpair_retro/", unpair_retro_game, name="unpair_retro_game"),

    path("game/<int:game_id>/add-link-source/", add_link_source, name="add_link_source"),

    path("game/<int:game_id>/remove-link/<int:link_id>/", remove_game_link, name="remove_game_link"),


]