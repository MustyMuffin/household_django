from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import ScheduledItem
from chores.utils import process_chore_completion


def claim_scheduled_task(item, user):
    if item.user is not None:
        return False, "❌ This task is already claimed."
    if item.completed:
        return False, "✅ This task has already been completed."

    item.user = user
    item.save()
    return True, f"✅ You have claimed: {item.title}"


def complete_scheduled_task(item, user, request=None):
    if item.user != user:
        return False, "❌ You can only complete tasks assigned to you."

    if item.completed:
        return False, "✅ This task is already completed."

    item.completed = True
    item.save()

    if item.content_type and item.object_id:
        try:
            chore = item.content_type.get_object_for_this_type(id=item.object_id)
            _, result, _, _ = process_chore_completion(user=user, chore=chore, request=request)
            return True, f"✅ Completed task: {item.title} (+{result['xp_awarded']} XP)"
        except Exception as e:
            return False, f"❌ Could not log chore: {e}"
    else:
        return True, "⚠️ Task completed, but no chore data was linked."