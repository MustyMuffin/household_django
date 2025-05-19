from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now, is_aware, localtime
from chores.models import Chore
from django.contrib.auth.models import Group, User
from datetime import timedelta, datetime, time

class ScheduleChoreForm(forms.Form):
    chore = forms.ModelChoiceField(queryset=Chore.objects.all(), label="Chore")
    assign_to = forms.ChoiceField(label="Assign To")
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
        required=False,
        label="Recurrence"
    )

    repeat_count = forms.IntegerField(
        label="Number of times to repeat",
        initial=7,
        min_value=1,
        required=False
    )

    notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Timezone-aware here
        now_local = localtime(now())
        today = now_local.date()
        current_hour = now_local.hour
        current_minute = now_local.minute

        worker_group = Group.objects.get(name='Workers')
        privileged_group = Group.objects.get(name='Privileged')
        users = (worker_group.user_set.all() |
                 privileged_group.user_set.all() |
                 User.objects.filter(pk=user.pk)).distinct()

        choices = [("anyone", "Anyone (Claimable by Any User)")]
        choices += [(str(u.pk), f"{u.get_full_name() or u.username}") for u in users]
        self.fields['assign_to'].choices = choices

        allow_today = current_hour < 20 or (current_hour == 20 and current_minute < 30)
        day_choices = []
        for i in range(7):
            day = today + timedelta(days=i)
            if i == 0 and not allow_today:
                continue
            label = day.strftime('%A (%b %d)')
            day_choices.append((day.isoformat(), label))
        self.fields['scheduled_day'].choices = day_choices

        if self.is_bound:
            selected_day_str = self.data.get('scheduled_day')
            try:
                selected_day = datetime.strptime(selected_day_str, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                selected_day = today
        else:
            selected_day = today

        # Time dropdown (9 AM to 9 PM in 30-minute steps) need to parameterize base_hours into scheduling settings model
        time_choices = []
        base_hours = range(9, 21)
        now_time = now_local.replace(second=0, microsecond=0).time()

        for hour in base_hours:
            for minute in (0, 30):
                t = time(hour=hour, minute=minute)
                if selected_day == today and t <= now_time:
                    continue
                label = t.strftime('%I:%M %p')
                time_choices.append((t.strftime('%H:%M'), label))

        if not time_choices:
            next_day = today + timedelta(days=1)
            for hour in base_hours:
                for minute in (0, 30):
                    t = time(hour=hour, minute=minute)
                    label = t.strftime('%I:%M %p')
                    time_choices.append((t.strftime('%H:%M'), label))
            self.initial['scheduled_day'] = next_day.isoformat()

        self.fields['scheduled_time'].choices = time_choices

        if not self.is_bound and time_choices:
            self.initial['scheduled_time'] = time_choices[0][0]




