from django.contrib.auth.models import User, Group
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ScheduledItem(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    completed = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    scheduled_for = models.DateTimeField()
    added_to_todo = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    recurring_set = models.ForeignKey(
        'RecurringSet', null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )

class TodoItem(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    scheduled_for = models.DateTimeField()
    completed = models.BooleanField(default=False)
    related_object_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_object_type', 'related_object_id')

class RecurringSet(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    recurrence_pattern = models.CharField(max_length=20)
    repeat_count = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.recurrence_pattern} × {self.repeat_count} by {self.created_by.username}"
