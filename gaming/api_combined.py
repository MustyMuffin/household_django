from .api.trueachievements import fetch_game_data_trueachievements
# from .api.steam import fetch_game_data_steam
from .api.retroachievements import fetch_game_data_retro
from .api.igdb import fetch_game_data_igdb

def fetch_game_data(title, source, progress_user=None):
    if source == "trueachievements":
        return fetch_game_data_trueachievements(title)
    elif source == "retroachievements":
        return fetch_game_data_retro(title, progress_user=progress_user)
    elif source == "steam":
        return fetch_game_data_steam(title)
    elif source == "igdb":
        return fetch_game_data_igdb(title)
    else:
        return None