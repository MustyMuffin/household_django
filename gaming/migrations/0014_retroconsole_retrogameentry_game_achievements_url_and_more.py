# Generated by Django 5.2.1 on 2025-06-08 20:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0013_collectibletype_usercollectibleprogress'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RetroConsole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('console_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RetroGameEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('retro_id', models.IntegerField(unique=True)),
                ('title', models.CharField(max_length=255)),
                ('console_id', models.IntegerField()),
                ('console_name', models.CharField(max_length=100)),
                ('image_url', models.URLField(blank=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='game',
            name='achievements_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='retrogamecache',
            name='achievements',
            field=models.JSONField(default=list),
        ),
        migrations.CreateModel(
            name='GameLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(max_length=50)),
                ('url', models.URLField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='gaming.game')),
            ],
        ),
        migrations.AddField(
            model_name='game',
            name='retro_game',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gaming.retrogameentry'),
        ),
        migrations.CreateModel(
            name='UserGameAchievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('retro_id', models.IntegerField()),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('points', models.IntegerField(default=0)),
                ('unlocked', models.BooleanField(default=False)),
                ('unlocked_at', models.DateTimeField(blank=True, null=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gaming.game')),
                ('game_progress', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gaming.gameprogress')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Game Achievement',
                'verbose_name_plural': 'Game Achievements',
                'indexes': [models.Index(fields=['user', 'game'], name='gaming_user_user_id_75d3c5_idx'), models.Index(fields=['retro_id'], name='gaming_user_retro_i_0642fe_idx'), models.Index(fields=['unlocked'], name='gaming_user_unlocke_007678_idx')],
                'unique_together': {('user', 'game', 'retro_id', 'title')},
            },
        ),
    ]
