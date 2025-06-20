# Generated by Django 5.2.1 on 2025-06-09 21:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book_club', '0010_rename_text_book_title'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bookprogresstracker',
            name='want_to_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='booksread',
            name='book_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='book_club.book'),
        ),
        migrations.AlterUniqueTogether(
            name='booksread',
            unique_together={('user', 'book_name')},
        ),
    ]
