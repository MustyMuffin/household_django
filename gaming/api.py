import requests
from decouple import config

APIFY_TOKEN = config('APIFY_TOKEN')
TASK_ID = 'mustymuffin/trueachievements-scraper-task'

def get_trueachievements_data():
    url = f'https://api.apify.com/v2/actor-tasks/{TASK_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []