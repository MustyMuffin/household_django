from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now
from chores.models import Chore
from django.contrib.auth.models import Group, User
from datetime import timedelta, datetime, time

class ScheduleChoreForm(forms.Form):
    chore = forms.ModelChoiceField(queryset=Chore.objects.all())

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
        required=False
    )

    repeat_count = forms.IntegerField(
        label="Number of times to repeat",
        initial=7,
        min_value=1,
        required=False
    )

    notes = forms.CharField(widget=forms.Textarea, required=False)


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # 🧑 Assign to: "Anyone" + individual users
        worker_group = Group.objects.get(name='Workers')
        parent_group = Group.objects.get(name='Parents')

        users = (worker_group.user_set.all() |
                parent_group.user_set.all() |
                User.objects.filter(pk=user.pk)).distinct()

        choices = [("anyone", "Anyone (Claimable by Any User)")]
        choices += [(str(u.pk), f"{u.get_full_name() or u.username}") for u in users]
        self.fields['assign_to'].choices = choices

        day_choices = []
        today = now().date()
        current_hour = now().hour
        current_minute = now().minute
        allow_today = current_hour < 20 or (current_hour == 20 and current_minute < 30)

        for i in range(7):
            day = today + timedelta(days=i)
            if i == 0 and not allow_today:
                continue
            label = day.strftime('%A (%b %d)')
            day_choices.append((day.isoformat(), label))
        self.fields['scheduled_day'].choices = day_choices

        selected_day_str = self.data.get('scheduled_day')
        try:
            selected_day = datetime.strptime(selected_day_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            selected_day = today

        time_choices = []
        base_hours = range(9, 21)  # 9 AM to 8:30 PM
        for hour in base_hours:
            for minute in (0, 30):
                if selected_day == today:
                    current = now().time()
                    slot = time(hour=hour, minute=minute)
                    if slot <= current:
                        continue
                t = time(hour=hour, minute=minute)
                label = t.strftime('%I:%M %p')
                time_choices.append((t.strftime('%H:%M'), label))

        if not time_choices:
            for hour in base_hours:
                for minute in (0, 30):
                    t = time(hour=hour, minute=minute)
                    label = t.strftime('%I:%M %p')
                    time_choices.append((t.strftime('%H:%M'), label))

        self.fields['scheduled_time'].choices = time_choices

        if not self.is_bound:
            next_minute = 30 if current_minute < 30 else 0
            next_hour = current_hour + (1 if current_minute >= 30 else 0)
            if next_hour < 21:
                self.initial['scheduled_time'] = f"{next_hour:02d}:{next_minute:02d}"




