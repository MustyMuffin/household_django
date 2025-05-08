from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.db import connection
from django.apps import apps
from django.contrib.auth.models import User

# Ensure UserStats is created only if the table exists and user is newly created
@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if not created:
        return  # Only run on user creation

    if "accounts_userstats" in connection.introspection.table_names():
        UserStats = apps.get_model("accounts", "UserStats")
        UserStats.objects.get_or_create(user=instance)
    else:
        print("⚠️ Skipped creating UserStats: table does not exist yet.")


# Create default XP settings after migration, if they don't already exist
@receiver(post_migrate)
def create_default_xp_settings(sender, **kwargs):
    if "accounts_xpsettings" in connection.introspection.table_names():
        from accounts.models import XPSettings
        if not XPSettings.objects.exists():
            XPSettings.objects.create(base=50, exponent=0.75)
            print("✅ Default XPSettings created after migration.")
        else:
            print("ℹ️ XPSettings already exists. No action needed.")
    else:
        print("⚠️ Skipped creating XPSettings: table does not exist yet.")

