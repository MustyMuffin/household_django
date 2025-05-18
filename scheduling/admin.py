from django.contrib import admin
from .models import ScheduledItem, TodoItem
from django.utils.timezone import localtime

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
