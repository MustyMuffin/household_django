# Generated by Django 5.1.2 on 2024-10-20 04:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('household_main', '0003_rename_topic_notes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entry',
            old_name='topic',
            new_name='notes',
        ),
    ]
