from django.urls import path
from .views import schedule_chore_view, todo_preview_view, todo_calendar_view, todo_calendar_json, claim_scheduled_item


urlpatterns = [
    path('schedule/', schedule_chore_view, name='schedule_chore'),
    path('todo-preview/<int:user_id>/', todo_preview_view, name='todo_preview'),
    path('calendar/', todo_calendar_view, name='todo_calendar'),
    path('calendar-json/', todo_calendar_json, name='todo_calendar_json'),\
    path('claim/<int:item_id>/', claim_scheduled_item, name='claim_scheduled_item'),
]
