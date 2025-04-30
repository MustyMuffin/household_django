from django.contrib import admin
from .models import UserStats, XPLog, XPSettings, BadgeType, Badge, UserBadge

admin.site.register(UserStats)
admin.site.register(XPLog)

@admin.register(XPSettings)
class XPSettingsAdmin(admin.ModelAdmin):
    list_display = ('base', 'exponent')

@admin.register(BadgeType)
class BadgeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "icon", "module", "milestone_type", "milestone_value")
    list_filter = ("module",)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    list_filter = ("badge",)