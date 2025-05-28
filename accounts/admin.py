from accounts.views import get_milestone_options
from django.db import connection
from django.contrib import admin
from django.urls import path
from .forms import BadgeMilestoneForm
from .models import (UserStats, XPLog, XPSettings, Badge,
                     UserBadge, XPTable)

admin.site.register(XPLog)
# admin.site.register(XPTable)
# admin.site.register(ChoreXPTable)
# admin.site.register(ReadingXPTable)

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ("user", "ra_username")
    search_fields = ("user__username", "ra_username")

@admin.register(XPSettings)
class XPSettingsAdmin(admin.ModelAdmin):
    list_display = ('base', 'exponent', 'locked')

    # def save_model(self, request, obj, form, change):
    #     super().save_model(request, obj, form, change)
    #     if obj.locked:
    #         XPLevelTable.objects.all().delete()
    #         for level in range(1, 101):
    #             xp = int(obj.base * (level ** obj.exponent))
    #             XPLevelTable.objects.create(level=level, xp_required=xp)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "icon", "app_label", "milestone_type", "milestone_value")
    list_filter = ("app_label",)

    print("✅ BadgeAdmin loaded")

    form = BadgeMilestoneForm

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "milestone_options/",
                self.admin_site.admin_view(get_milestone_options),
                name="accounts_badge_milestone_options",
            ),
        ]
        return custom_urls + urls


def get_changeform_template(request, obj=None, **kwargs):
    return 'accounts/templates/admin/accounts/badge/change_form.html'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    list_filter = ("badge",)
