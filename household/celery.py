import os
from celery import Celery
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household.settings')

app = Celery('household')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

import logging
logger = logging.getLogger('celery')
logger.setLevel('DEBUG')

def debug_task_discovery():
    print(">>> Debugging Celery autodiscovery")
    from importlib import import_module
    for app_name in app.conf.include or []:
        print(f"Checking app: {app_name}")
        try:
            import_module(f"{app_name}.tasks")
            print(f"✓ Found: {app_name}.tasks")
        except ModuleNotFoundError:
            print(f"✗ No tasks.py in {app_name}")
        except Exception as e:
            print(f"✗ Error importing {app_name}.tasks: {e}")

debug_task_discovery()

