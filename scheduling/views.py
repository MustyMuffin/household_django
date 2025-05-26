from itertools import chain

from django.urls import reverse
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import ScheduledItem, RecurringSet, Notification
from django.utils.timezone import now, timedelta
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ScheduleChoreForm
# from .tasks import add_due_chores_to_todo
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .helpers import claim_scheduled_task, complete_scheduled_task

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

@login_required
def upcoming_tasks_view(request):
    filter_type = request.GET.get("filter", "all")
    start = now()
    end = start + timedelta(days=14) # Add to scheduling settings later

    items = ScheduledItem.objects.filter(scheduled_for__range=(start, end)).order_by("scheduled_for")

    if filter_type == "claimed":
        items = items.filter(user__isnull=False)
    elif filter_type == "unclaimed":
        items = items.filter(user__isnull=True)

    users = User.objects.all()

    return render(request, "scheduling/upcoming_tasks.html", {
        "items": items,
        "filter": filter_type,
        "users": users,
    })

@login_required
def read_and_redirect_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect(notification.url or "/")

@login_required
def assign_scheduled_task(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    if request.method == "POST":
        assignee_id = request.POST.get("assignee_id")
        try:
            assignee = User.objects.get(pk=assignee_id)
        except User.DoesNotExist:
            messages.error(request, "❌ User not found.")
            return redirect("scheduling:upcoming_tasks")

        is_privileged = request.user.groups.filter(name="Privileged").exists()

        if item.user and not is_privileged:
            messages.error(request, "❌ Task is already assigned and cannot be reassigned.")
            return redirect("scheduling:upcoming_tasks")

        item.user = assignee
        item.save()

        Notification.objects.create(
            user=assignee,
            message=f"📌 You’ve been assigned to: {item.title} scheduled for {item.scheduled_for.strftime('%A %b %d @ %I:%M %p')}",
            url=f"/scheduling/calendar/?highlight={item.id}"
        )

        messages.success(request, f"✅ Task '{item.title}' assigned to {assignee.username}.")
        return redirect("scheduling:upcoming_tasks")

    messages.error(request, "❌ Invalid request method.")
    return redirect("scheduling:upcoming_tasks")

    return redirect('scheduling:upcoming_tasks')

@login_required
@user_passes_test(is_privileged)
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
            repeat_count = form.cleaned_data.get('repeat_count') or 7


            assign_to_value = form.cleaned_data["assign_to"]
            notes = form.cleaned_data.get("notes", "")

            if assign_to_value == "anyone":
                assigned_user = None
                assigned_group = None
                notification_recipient = None  # no one specific
            else:
                assigned_user = User.objects.get(pk=assign_to_value)
                assigned_group = None
                notification_recipient = assigned_user

            # Recurrence logic
            for i in range(repeat_count):
                if recurrence == 'none' and i > 0:
                    break

                delta_days = {
                    'daily': i,
                    'every_other': i * 2,
                    'every_2': i * 2,
                    'every_3': i * 3,
                    'weekly': i * 7,
                    'monthly': i * 30
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

                item = ScheduledItem.objects.create(
                    user=assign_to if isinstance(assign_to, User) else None,
                    group=assign_to if isinstance(assign_to, Group) else None,
                    content_type=ContentType.objects.get_for_model(chore),
                    object_id=chore.id,
                    scheduled_for=item_time,
                    notes=notes,
                    recurring_set=recurring_set
                )

            # add_due_chores_to_todo.delay()

            calendar_url = reverse('scheduling:todo_calendar') + f'?highlight={item.id}'

            if notification_recipient:
                Notification.objects.create(
                    user=notification_recipient,
                    message=f"You’ve been assigned a task: {chore.text} on {item_time.strftime('%A %b %d @ %I:%M %p')}",
                    url=calendar_url,
                )
            else:
                recipient_groups = Group.objects.filter(name__in=['Workers', 'Privileged'])
                all_recipients = set(chain.from_iterable(group.user_set.all() for group in recipient_groups))

                for user in all_recipients:
                    Notification.objects.create(
                        user=user,
                        message=f"📝 '{chore.text}' on {item_time.strftime('%A %b %d @ %I:%M %p')} is available to claim.",
                        url=calendar_url,
                    )


            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"'{getattr(chore, 'text', str(chore))}' scheduled"
                })

            messages.success(request, f"'{getattr(chore, 'text', str(chore))}' scheduled")
            return redirect('scheduling:todo_calendar')
    else:
        form = ScheduleChoreForm(user=request.user)
    return render(request, 'scheduling/schedule_chore.html', {'form': form})

@login_required
def all_notifications_view(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'scheduling/all_notifications.html', {
        'notifications': notifications,
    })

@login_required
def clear_all_notifications(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def todo_preview_view(request, user_id):
    upcoming = now() + timedelta(days=7)
    todos = ScheduledItem.objects.filter(
        user_id=user_id,
        completed=False,
        scheduled_for__lte=upcoming
    ).order_by('scheduled_for')[:10]

    html = render_to_string('scheduling/todo_preview.html', {'todos': todos})
    return HttpResponse(html)

@login_required
def todo_calendar_view(request):
    return render(request, 'scheduling/todo_calendar.html')

@login_required
def todo_calendar_json(request):
    user = request.user
    user_group_ids = set(user.groups.values_list('id', flat=True))

    todos = ScheduledItem.objects.filter(completed=False)

    events = []

    for todo in todos:
        claimable = todo.user is None

        events.append({
            "id": todo.id,
            "title": f"{todo.title} - Unclaimed" if todo.user is None else f"{todo.title} - {todo.user}",
            "start": todo.scheduled_for.isoformat(),
            "color": "#ff4444" if todo.scheduled_for < now() else "#3788d8",
            "claimable": todo.user is None,
            "assignedTo": todo.user.username if todo.user else None,
            "assignedToProfilePic": todo.user.userstats.profile_picture.url if todo.user and hasattr(todo.user, "userstats") and todo.user.userstats.profile_picture else None,
        })

    return JsonResponse(events, safe=False)

@login_required
def claim_and_complete_task(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    if item.user is None:
        claimed, claim_msg = claim_scheduled_task(item, request.user)
        messages.info(request, claim_msg)
        if not claimed:
            return redirect('scheduling:todo_calendar')

    completed, complete_msg = complete_scheduled_task(item, request.user, request)
    messages.info(request, complete_msg)

    return redirect('scheduling:todo_calendar')

@login_required
def claim_scheduled_item(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    success, message = claim_scheduled_task(item, request.user)
    messages.info(request, message)

    return redirect('scheduling:todo_calendar')


@login_required
def complete_scheduled_item(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    success, message = complete_scheduled_task(item, request.user, request)
    messages.info(request, message)

    return redirect('scheduling:todo_calendar')

@login_required
def delete_scheduled_task(request, item_id):
    item = get_object_or_404(ScheduledItem, id=item_id)

    if not request.user.groups.filter(name="Privileged").exists():
        messages.error(request, "You don’t have permission to delete this task.")
        return redirect('scheduling:upcoming_tasks')

    item.delete()
    messages.success(request, "🗑️ Task deleted successfully.")
    return redirect('scheduling:upcoming_tasks')

@login_required
def rescind_scheduled_item(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    if item.user != request.user:
        messages.error(request, "❌ You can only rescind tasks assigned to you.")
        return redirect('scheduling:todo_calendar')

    if item.completed:
        messages.warning(request, "⚠️ You cannot rescind a completed task.")
        return redirect('scheduling:todo_calendar')

    item.user = None
    item.save()

    messages.success(request, "↩️ Task has been rescinded and is now unclaimed.")
    return redirect('scheduling:todo_calendar')






