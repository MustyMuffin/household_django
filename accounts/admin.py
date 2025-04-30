from django.contrib import admin
from .models import UserStats, XPLog, XPSettings, Badge, UserBadge
from django.http import JsonResponse
from chores.models import Chore

admin.site.register(UserStats)
admin.site.register(XPLog)

from .forms import ModuleBadgeConfigForm, BadgeMilestoneForm


@admin.register(XPSettings)
class XPSettingsAdmin(admin.ModelAdmin):
    list_display = ('base', 'exponent')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "icon", "milestone_type", "milestone_value")
    list_filter = ("app_label","milestone_type")
    form = ModuleBadgeConfigForm
    form = BadgeMilestoneForm

    class Media:
        js = ('admin/js/badge_dynamic.js',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    list_filter = ("badge",)

def get_milestone_options(request):
    app = request.GET.get("app")
    choices = []

    if app == "chores":
        choices = [{"value": chore.id, "label": chore.text} for chore in Chore.objects.all()]

    return JsonResponse({"choices": choices})
