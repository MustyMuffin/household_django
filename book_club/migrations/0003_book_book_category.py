# Generated by Django 5.1.2 on 2025-04-21 22:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book_club', '0002_bookcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='book_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='book_club.bookcategory'),
        ),
    ]
