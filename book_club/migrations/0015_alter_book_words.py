# Generated by Django 5.2.1 on 2025-06-11 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book_club', '0014_alter_book_pages_alter_bookmetadata_pages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='words',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
