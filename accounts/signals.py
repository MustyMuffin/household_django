from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.db import connection
from django.apps import apps
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import XPSettings, XPTable, ChoreXPTable, ReadingXPTable


@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if not created:
        return  # Only run on user creation

    if "accounts_userstats" in connection.introspection.table_names():
        UserStats = apps.get_model("accounts", "UserStats")
        UserStats.objects.get_or_create(user=instance)
    else:
        print("Skipped creating UserStats: table does not exist yet.")


@receiver(post_migrate)
def create_default_xp_settings(sender, **kwargs):
    if "accounts_xpsettings" in connection.introspection.table_names():
        from accounts.models import XPSettings
        if not XPSettings.objects.exists():
            XPSettings.objects.create(base=50, exponent=0.75)
            print("Default XPSettings created after migration.")
        else:
            print("ℹXPSettings already exists. No action needed.")
    else:
        print("Skipped creating XPSettings: table does not exist yet.")

@receiver(post_save, sender=XPSettings)
def generate_xp_tables(sender, instance, created, **kwargs):
    base = instance.base
    curve = instance.exponent
    chore_base = instance.chore_base
    chore_curve = instance.chore_exponent
    reading_base = instance.reading_base
    reading_curve = instance.reading_exponent
    max_level = 100

    XPTable.objects.all().delete()
    ChoreXPTable.objects.all().delete()
    ReadingXPTable.objects.all().delete()

    with connection.cursor() as cursor:
        db_engine = connection.vendor
        if db_engine == 'sqlite':
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='accounts_xptable';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='accounts_chorexptable';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='accounts_readingxptable';")
        elif db_engine == 'postgresql':
            cursor.execute("ALTER SEQUENCE accounts_xptable_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE accounts_chorexptable_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE accounts_readingxptable_id_seq RESTART WITH 1;")

    XPTable.objects.bulk_create([
        XPTable(overall_level=level, xp_required=int(base * (level ** curve)))
        for level in range(2, max_level + 1)
    ])

    ChoreXPTable.objects.bulk_create([
        ChoreXPTable(chore_level=level, chore_xp_required=int(chore_base * (level ** chore_curve)))
        for level in range(2, max_level + 1)
    ])

    ReadingXPTable.objects.bulk_create([
        ReadingXPTable(reading_level=level, reading_xp_required=int(reading_base * (level ** reading_curve)))
        for level in range(2, max_level + 1)
    ])

    from .xp_utils import XPManager
    XPManager.clear_cache()
    XPManager.resync_all_user_levels()

    print(f"✅ XP tables regenerated (base={base}, curve={curve})")


