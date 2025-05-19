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
from .tasks import add_due_chores_to_todo
from django.contrib.auth.models import Group, User
from chores.models import ChoreEntry
from django.shortcuts import get_object_or_404, redirect, render
from chores.utils import process_chore_completion
from django.views.decorators.http import require_POST

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

@login_required
def test_notification(request):
    Notification.objects.create(
        user=request.user,
        message="🔔 Test notification sent via view!",
        read=False
    )
    return redirect("scheduling:upcoming_tasks")

@login_required
def upcoming_tasks_view(request):
    filter_type = request.GET.get("filter", "all")
    start = now()
    end = start + timedelta(days=30)

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

@require_POST
@login_required
def assign_scheduled_task(request, item_id):
    item = get_object_or_404(ScheduledItem, id=item_id)
    if item.user is not None:
        messages.error(request, "❌ This task is already claimed.")
        return redirect('scheduling:upcoming_tasks')

    assignee_id = request.POST.get("assignee_id")
    try:
        assignee = User.objects.get(pk=assignee_id)
    except User.DoesNotExist:
        messages.error(request, "❌ Invalid user selected.")
        return redirect('scheduling:upcoming_tasks')

    item.user = assignee
    item.save()

    formatted_date = item.scheduled_for.strftime("%A, %b %d at %I:%M %p")
    messages.success(request, f"✅ Assigned task '{item.title}' on {formatted_date} to {assignee.username}.")

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

            add_due_chores_to_todo.delay()

            calendar_url = reverse('scheduling:todo_calendar') + f'?highlight={item.id}'

            if notification_recipient:
                Notification.objects.create(
                    user=notification_recipient,
                    message=f"You’ve been assigned a task: {chore.text} on {item_time.strftime('%A %b %d @ %I:%M %p')}",
                    url=f"{reverse('scheduling:todo_calendar')}?highlight={item.id}",
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

    todos = ScheduledItem.objects.filter(
        completed=False
    ).filter(
        models.Q(user=user) |
        models.Q(user__isnull=True)
    )

    events = []

    for todo in todos:
        claimable = todo.user is None

        events.append({
            "id": todo.id,
            "title": f"[Unclaimed] {todo.title}" if todo.user is None else todo.title,
            "start": todo.scheduled_for.isoformat(),
            "color": "#ff4444" if todo.scheduled_for < now() else "#3788d8",
            "claimable": todo.user is None,
            "assignedTo": todo.user.username if todo.user else None,
        })

    return JsonResponse(events, safe=False)

@login_required
def complete_scheduled_item(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    if item.user != request.user:
        messages.error(request, "❌ You can only complete tasks assigned to you.")
        return redirect('scheduling:todo_calendar')

    if item.completed:
        messages.info(request, "✅ This task is already completed.")
        return redirect('scheduling:todo_calendar')

    item.completed = True
    item.save()

    try:
        if item.content_type and item.object_id:
            chore = item.content_type.get_object_for_this_type(id=item.object_id)
            _, result, _, _ = process_chore_completion(user=request.user, chore=chore, request=request)
            messages.success(request, f"✅ Completed task: {item.title} (+{result['xp_awarded']} XP)")
        else:
            messages.warning(request, "⚠️ Task completed, but no chore data was linked.")
    except Exception as e:
        messages.error(request, f"❌ Could not log chore: {e}")

    return redirect('scheduling:todo_calendar')


@login_required
def claim_scheduled_item(request, item_id):
    item = get_object_or_404(ScheduledItem, pk=item_id)

    if item.user is not None:
        messages.error(request, "❌ This task is already claimed.")
        return redirect(reverse('scheduling:todo_calendar'))

    if item.completed:
        messages.info(request, "✅ This task has already been completed.")
        return redirect(reverse('scheduling:todo_calendar'))

    item.user = request.user
    item.save()

    messages.success(request, f"✅ You have claimed: {item.title}")
    return redirect(reverse('scheduling:todo_calendar'))






