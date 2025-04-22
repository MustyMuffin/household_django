from django.contrib import admin

from .models import UserStats, XPLog

admin.site.register(UserStats)
admin.site.register(XPLog)