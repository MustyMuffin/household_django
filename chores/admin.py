from django.contrib import admin
from .models import Chore
from scheduling.models import ScheduledItem
from django.contrib.contenttypes.models import ContentType

from .models import Chore, EarnedWage, ChoreCategory, ChoreEntry

admin.site.register(Chore)
admin.site.register(ChoreEntry)
admin.site.register(EarnedWage)
admin.site.register(ChoreCategory)

class ChoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by')
    actions = ['schedule_chore_for_user']

    def schedule_chore_for_user(self, request, queryset):
        # Example: hardcoded user ID for simplicity (replace with form/dialog in production)
        user = request.user  # or use a custom superuser-only form
        content_type = ContentType.objects.get_for_model(Chore)

        for chore in queryset:
            ScheduledItem.objects.create(
                user=user,  # or another selected user
                content_type=content_type,
                object_id=chore.id,
                scheduled_for=timezone.now() + timezone.timedelta(days=1),
                notes=f"Scheduled by {request.user.username}"
            )

        self.message_user(request, f"{queryset.count()} chores scheduled.")
    schedule_chore_for_user.short_description = "Schedule chore for user (example)"
