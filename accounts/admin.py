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
    list_display = ("name", "badge_type", "xp_required", "words_required", "chores_completed_required")
    list_filter = ("badge_type",)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "date_earned")
    list_filter = ("badge__badge_type",)