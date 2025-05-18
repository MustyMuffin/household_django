import datetime

from django.db import models
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import ScheduledItem, TodoItem
from django.utils.timezone import now, timedelta
from django.utils.timezone import make_aware
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ScheduleChoreForm
from .models import ScheduledItem, RecurringSet
from .tasks import add_due_chores_to_todo
from django.contrib.auth.models import Group, User

def is_parent(user):
    return user.groups.filter(name='Parents').exists()

@login_required
@user_passes_test(is_parent)
def schedule_chore_view(request):
    if request.method == 'POST':
        form = ScheduleChoreForm(request.POST or None, user=request.user)
        if form.is_valid():
            chore = form.cleaned_data['chore']

            assign_to = form.cleaned_data['assign_to']
            user = None
            group = None

            if assign_to.startswith("user:"):
                user_id = int(assign_to.split(":")[1])
                user = User.objects.get(pk=user_id)
            elif assign_to.startswith("group:"):
                group_id = int(assign_to.split(":")[1])
                group = Group.objects.get(pk=group_id)

            from django.utils.dateparse import parse_datetime, parse_time
            from datetime import timedelta, datetime
            from django.utils.timezone import make_aware

            selected_day = form.cleaned_data['scheduled_day']  # "YYYY-MM-DD"
            selected_time = form.cleaned_data['scheduled_time']  # "HH:MM"
            scheduled_for = make_aware(datetime.strptime(f"{selected_day} {selected_time}", "%Y-%m-%d %H:%M"))

            scheduled_items = ScheduledItem.objects.filter(
                scheduled_for__lte=now(),
                user__isnull=False,
                completed=False,
            )

            recurrence = form.cleaned_data.get('recurrence', 'none')
            notes = form.cleaned_data['notes']
            repeat_count = form.cleaned_data.get('repeat_count') or 7  # default to 7

            assign_to_value = form.cleaned_data['assign_to']

            if assign_to_value == "anyone":
                user = None
                group = None
            else:
                user = User.objects.get(pk=int(assign_to_value))
                group = None  # optional, just to be explicit

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

                if recurrence != 'none':
                    recurring_set = RecurringSet.objects.create(
                    created_by=request.user,
                    recurrence_pattern=recurrence,
                    repeat_count=repeat_count,
                    notes=notes
                )
                else:
                    recurring_set = None

                ScheduledItem.objects.create(
                    user=user,
                    group=None,
                    content_type=ContentType.objects.get_for_model(chore),
                    object_id=chore.id,
                    scheduled_for=item_time,
                    notes=notes,
                    recurring_set=recurring_set
                )

            add_due_chores_to_todo.delay()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"'{getattr(chore, 'text', str(chore))}' scheduled"
                })

            messages.success(request, f"'{getattr(chore, 'text', str(chore))}' scheduled")
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
    user = request.user
    user_group_ids = set(user.groups.values_list('id', flat=True))

    todos = TodoItem.objects.filter(
        completed=False
    ).filter(
        models.Q(user=user) |
        models.Q(user__isnull=True)
    )

    events = []

    for todo in todos:
        claimable = todo.user is None

        print("DEBUG TODO:", {
            "todo.id": todo.id,
            "todo.title": todo.title,
            "todo.user": todo.user,
            "todo.group_id": todo.group_id,
            "user_group_ids": user_group_ids,
            "claimable": todo.user is None and todo.group_id in user_group_ids
        })

        events.append({
            "id": todo.id,
            "title": f"{todo.title}" if todo.user else f"[Unclaimed] {todo.title}",
            "start": todo.scheduled_for.isoformat(),
            "color": "#ff4444" if todo.scheduled_for < now() else "#3788d8",
            "claimable": claimable
        })

    return JsonResponse(events, safe=False)


@login_required
def claim_scheduled_item(request, item_id):
    item = get_object_or_404(TodoItem, pk=item_id)

    if item.user is None:
        item.user = request.user
        item.group = None
        item.save()
        messages.success(request, "✅ You have claimed this task.")
    else:
        messages.error(request, "❌ This task has already been claimed.")

    return redirect('todo_calendar')





