from django.urls import path

from .views import (
    schedule_chore_view, todo_preview_view, todo_calendar_view, todo_calendar_json,
    complete_scheduled_item, claim_scheduled_item, upcoming_tasks_view,
    assign_scheduled_task, read_and_redirect_notification,
    all_notifications_view, claim_and_complete_task, delete_scheduled_task,
    rescind_scheduled_item, clear_all_notifications,
)

app_name = "scheduling"

urlpatterns = [
    path('schedule/', schedule_chore_view, name='schedule_chore'),
    path('todo-preview/<int:user_id>/', todo_preview_view, name='todo_preview'),
    path('calendar/', todo_calendar_view, name='todo_calendar'),
    path('calendar-json/', todo_calendar_json, name='todo_calendar_json'),
    path('complete/<int:item_id>/', complete_scheduled_item, name='complete_scheduled_item'),
    path('claim/<int:item_id>/', claim_scheduled_item, name='claim_scheduled_item'),
    path("upcoming/", upcoming_tasks_view, name="upcoming_tasks"),
    path("assign/<int:item_id>/", assign_scheduled_task, name="assign_scheduled_task"),
    path('notifications/read/<int:notification_id>/', read_and_redirect_notification, name='read_notification'),
    path('notifications/', all_notifications_view, name='all_notifications'),
    path("notifications/clear_all/", clear_all_notifications, name="clear_all_notifications"),
    path('claim-complete/<int:item_id>/', claim_and_complete_task, name='claim_and_complete'),
    path('delete/<int:item_id>/', delete_scheduled_task, name='delete_scheduled_task'),
    path('rescind/<int:item_id>/', rescind_scheduled_item, name='rescind_scheduled_item')

]
