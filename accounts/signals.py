from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserStats, XPSettings

@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if created:
        UserStats.objects.create(user=instance)

@receiver(post_migrate)
def create_default_xp_settings(sender, **kwargs):
    if sender.name == "accounts":
        if not XPSettings.objects.exists():
            XPSettings.objects.create(base=50, exponent=0.75)
            print("✅ Default XPSettings created after migration.")
        else:
            print("ℹ️ XPSettings already exists. No action needed.")