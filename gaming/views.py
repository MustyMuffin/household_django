from django.shortcuts import render
from django.core.cache import cache

def achievements_view(request):
    data = get_trueachievements_data()
    return render(request, "gaming/achievements.html", {"achievements": data})


def get_trueachievements_data():
    if (cached := cache.get("ta_data")) is not None:
        return cached
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cache.set("ta_data", data, 60 * 10)  # cache for 10 mins
        return data
    return []
