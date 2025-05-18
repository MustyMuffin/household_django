from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now
from chores.models import Chore
from django.contrib.auth.models import Group, User
from datetime import timedelta, datetime, time

class ScheduleChoreForm(forms.Form):
    chore = forms.ModelChoiceField(queryset=Chore.objects.all())
    assignee = forms.ModelChoiceField(queryset=User.objects.none())

    scheduled_day = forms.ChoiceField(label="Day")
    scheduled_time = forms.ChoiceField(label="Time")

    recurrence = forms.ChoiceField(
    choices=[
        ('none', 'None'),
        ('daily', 'Every Day'),
        ('every_other', 'Every Other Day'),
        ('every_2', 'Every 2 Days'),
        ('every_3', 'Every 3 Days'),
        ('weekly', 'Weekly (Same Day)'),
        ('monthly', 'Monthly (Same Date)')
    ],
    initial='none',
    required=False
    )

    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Allow scheduling for Workers and Parents
        worker_group = Group.objects.get(name='Workers')
        parent_group = Group.objects.get(name='Parents')
        self.fields['assignee'].queryset = (
            worker_group.user_set.all() |
            parent_group.user_set.all() |
            User.objects.filter(pk=user.pk)
        ).distinct()

        # Generate next 7 days for the "Day" dropdown
        day_choices = []
        today = now().date()
        for i in range(7):
            day = today + timedelta(days=i)
            label = day.strftime('%A (%b %d)')  # e.g. "Monday (May 20)"
            day_choices.append((day.isoformat(), label))
        self.fields['scheduled_day'].choices = day_choices

        # Generate time choices from 9am to 9pm
        time_choices = []
        for hour in range(9, 22):  # 9 to 21 inclusive
            t = time(hour=hour)
            label = t.strftime('%I:%M %p')  # e.g. "09:00 AM"
            time_choices.append((t.strftime('%H:%M'), label))
        self.fields['scheduled_time'].choices = time_choices

        repeat_count = forms.IntegerField(
            label="Number of times to repeat",
            initial=7,
            min_value=1,
            required=False
        )

