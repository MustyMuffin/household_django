import datetime

from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import ScheduledItem, TodoItem
from django.utils.timezone import now, timedelta
from django.utils.timezone import make_aware
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ScheduleChoreForm
from .models import ScheduledItem
from .tasks import add_due_chores_to_todo

def is_parent(user):
    return user.groups.filter(name='Parents').exists()

@login_required
@user_passes_test(is_parent)
def schedule_chore_view(request):
    if request.method == 'POST':
        form = ScheduleChoreForm(request.POST or None, user=request.user)
        if form.is_valid():
            chore = form.cleaned_data['chore']
            user = form.cleaned_data['assignee']

            from django.utils.dateparse import parse_datetime

            from django.utils.dateparse import parse_datetime

            from datetime import timedelta, datetime
            from django.utils.dateparse import parse_time
            from django.utils.timezone import make_aware

            # Combine the selected day + time
            selected_day = form.cleaned_data['scheduled_day']  # "YYYY-MM-DD"
            selected_time = form.cleaned_data['scheduled_time']  # "HH:MM"
            scheduled_for = make_aware(datetime.strptime(f"{selected_day} {selected_time}", "%Y-%m-%d %H:%M"))

            recurrence = form.cleaned_data.get('recurrence', 'none')
            notes = form.cleaned_data['notes']
            repeat_count = form.cleaned_data.get('repeat_count') or 7  # default to 7

            # Recurrence logic
            for i in range(repeat_count):
                if recurrence == 'none' and i > 0:
                    break  # only create one

                delta_days = {
                    'daily': i,
                    'every_other': i * 2,
                    'every_2': i * 2,
                    'every_3': i * 3,
                    'weekly': i * 7,
                    'monthly': i * 30  # rough monthly approximation
                }.get(recurrence, 0)

                item_time = scheduled_for + timedelta(days=delta_days)

                ScheduledItem.objects.create(
                    user=user,
                    content_type=ContentType.objects.get_for_model(chore),
                    object_id=chore.id,
                    scheduled_for=item_time,
                    notes=notes
                )

            add_due_chores_to_todo.delay()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"'{getattr(chore, 'text', str(chore))}' scheduled for {user.username}"
                })

            messages.success(request, f"'{getattr(chore, 'text', str(chore))}' scheduled for {user.username}")
            return redirect('schedule_chore')
    else:
        form = ScheduleChoreForm(user=request.user)
    return render(request, 'scheduling/schedule_chore.html', {'form': form})

@login_required
@user_passes_test(is_parent)
def todo_preview_view(request, user_id):
    upcoming = now() + timedelta(days=7)
    todos = TodoItem.objects.filter(
        user_id=user_id,
        completed=False,
        scheduled_for__lte=upcoming
    ).order_by('scheduled_for')[:10]

    html = render_to_string('scheduling/todo_preview.html', {'todos': todos})
    return HttpResponse(html)

from django.http import JsonResponse
from .models import TodoItem

@login_required
def todo_calendar_view(request):
    return render(request, 'scheduling/todo_calendar.html')

@login_required
def todo_calendar_json(request):
    todos = TodoItem.objects.filter(completed=False)
    events = []
    for todo in todos:
        if todo.scheduled_for:
            events.append({
                "title": f"{todo.user.username}: {todo.title}",
                "start": todo.scheduled_for.isoformat(),
                "end": (todo.scheduled_for + timedelta(hours=1)).isoformat(),
                "id": todo.id,
                "color": "#ff4444" if todo.scheduled_for < now() else "#3788d8"
            })

    return JsonResponse(events, safe=False)




