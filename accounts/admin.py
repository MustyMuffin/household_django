from django.contrib import admin

from .models import UserStats, XPLog, XPSettings

admin.site.register(UserStats)
admin.site.register(XPLog)

@admin.register(XPSettings)
class XPSettingsAdmin(admin.ModelAdmin):
    list_display = ('base', 'exponent')