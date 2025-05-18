from django.contrib import admin
from .models import ScheduledItem, TodoItem
from django.utils.timezone import localtime
from .models import RecurringSet, ScheduledItem
from django.utils.timezone import now
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from datetime import timedelta


@admin.register(RecurringSet)
class RecurringSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_by', 'recurrence_pattern', 'repeat_count', 'created_at']
    actions = ['delete_entire_set', 'reschedule_set']

    def delete_entire_set(self, request, queryset):
        count = 0
        for rset in queryset:
            rset.items.all().delete()
            rset.delete()
            count += 1
        self.message_user(request, f"Deleted {count} recurring sets and their scheduled items.", messages.SUCCESS)
    delete_entire_set.short_description = "🗑️ Delete recurring set and all associated scheduled items"

    def reschedule_set(self, request, queryset):
        if 'apply' in request.POST:
            try:
                new_start = request.POST['new_start']
                parsed_start = forms.DateTimeField().clean(new_start)
                for rset in queryset:
                    pattern = rset.recurrence_pattern
                    count = rset.repeat_count
                    items = rset.items.order_by('scheduled_for')

                    for i, item in enumerate(items):
                        if pattern == 'daily':
                            item.scheduled_for = parsed_start + timedelta(days=i)
                        elif pattern == 'every_other':
                            item.scheduled_for = parsed_start + timedelta(days=i * 2)
                        elif pattern == 'every_2':
                            item.scheduled_for = parsed_start + timedelta(days=i * 2)
                        elif pattern == 'every_3':
                            item.scheduled_for = parsed_start + timedelta(days=i * 3)
                        elif pattern == 'weekly':
                            item.scheduled_for = parsed_start + timedelta(weeks=i)
                        elif pattern == 'monthly':
                            item.scheduled_for = parsed_start + timedelta(days=i * 30)  # rough approx
                        item.save()

                self.message_user(request, f"Rescheduled {queryset.count()} set(s).", messages.SUCCESS)
                return redirect(request.get_full_path())
            except Exception as e:
                self.message_user(request, f"Error: {e}", messages.ERROR)

        return render(request, 'admin/reschedule_set.html', {
            'sets': queryset,
            'title': 'Reschedule Selected Recurring Sets'
        })

    reschedule_set.short_description = "🔁 Reschedule recurring set"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reschedule-set/', self.admin_site.admin_view(self.reschedule_set), name='reschedule-set'),
        ]
        return custom_urls + urls

@admin.register(ScheduledItem)
class ScheduledItemAdmin(admin.ModelAdmin):
    list_display = ("user", "item_summary", "scheduled_for", "added_to_todo")
    list_filter = ("added_to_todo", "scheduled_for")
    search_fields = ("user__username", "notes")
    ordering = ("-scheduled_for",)

    def item_summary(self, obj):
        return str(obj.item)
    item_summary.short_description = "Scheduled Item"

@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "scheduled_for", "completed", "related_model")
    list_filter = ("completed",)
    search_fields = ("title", "user__username")
    ordering = ("-scheduled_for",)

    actions = ["mark_completed"]

    def mark_completed(self, request, queryset):
        updated = queryset.update(completed=True)
        self.message_user(request, f"{updated} tasks marked as completed.")
    mark_completed.short_description = "Mark selected tasks as completed"

    def related_model(self, obj):
        return str(obj.related_object) if obj.related_object else "-"
    related_model.short_description = "Linked Object"
