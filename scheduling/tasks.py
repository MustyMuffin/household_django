from celery import shared_task

from .models import Notification
from django.utils.timezone import now
from datetime import timedelta
from .models import ScheduledItem
from django.contrib.contenttypes.models import ContentType
from chores.models import Chore

@shared_task
def notify_due_tasks():
    upcoming_window = now() + timedelta(hours=1)
    tasks = ScheduledItem.objects.filter(
        completed=False,
        scheduled_for__range=(now(), upcoming_window),
        user__isnull=False
    ).select_related('user')

    for task in tasks:
        Notification.objects.get_or_create(
            user=task.user,
            message=f"Reminder: '{task.item}' is due at {task.scheduled_for.strftime('%I:%M %p')}",
        )
