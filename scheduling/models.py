from django.contrib.auth.models import User, Group
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

class ScheduledItem(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255, blank=True)
    scheduled_for = models.DateTimeField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    recurring_set = models.ForeignKey(
        'RecurringSet', null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )

    def save(self, *args, **kwargs):
        if not self.title and self.content_object:
            self.title = str(self.content_object)
        super().save(*args, **kwargs)

class RecurringSet(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    recurrence_pattern = models.CharField(max_length=20)
    repeat_count = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.recurrence_pattern} × {self.repeat_count} by {self.created_by.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    read = models.BooleanField(default=False)
    url = models.URLField(blank=True)

    def __str__(self):
        return f"To {self.user.username}: {self.message}"
