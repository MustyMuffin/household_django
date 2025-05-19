from celery import shared_task
from .models import Notification

@shared_task
def add_due_chores_to_todo():
    from django.utils.timezone import now
    from datetime import timedelta
    from .models import ScheduledItem, TodoItem
    from django.contrib.contenttypes.models import ContentType
    from chores.models import Chore

    start = now()
    end = start + timedelta(days=7)

    chore_type = ContentType.objects.get_for_model(Chore)

    due = ScheduledItem.objects.filter(
        content_type=chore_type,
        scheduled_for__range=(start, end),
        added_to_todo=False
    )

    for item in due:
        TodoItem.objects.create(
            user=item.user,
            title=f"Do chore: {item.item.text}",
            scheduled_for=item.scheduled_for,
            related_object=item.item
        )
        item.added_to_todo = True
        item.save()

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
