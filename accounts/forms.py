from django import forms
from .models import Badge
from chores.models import Chore
from .constants import ALLOWED_APPS

class ModuleBadgeConfigForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['app_label'].choices = [
            (key, label) for key, label in ALLOWED_APPS.items()
        ]

class BadgeMilestoneForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        app = self.initial.get('app_label') or self.data.get('app_label') or getattr(self.instance, 'app_label', None)
        print(f"[DEBUG] Initializing BadgeMilestoneForm with app_label={app}")
        if app == 'chores':
            self.fields['milestone_type'] = forms.ModelChoiceField(
                queryset=Chore.objects.all(),
                label='Chore Milestone',
                required=True
            )
        else:
            self.fields['milestone_type'] = forms.CharField(
                max_length=100,
                label='Milestone Type',
                help_text="Enter manually (e.g., number of books read) FUCK YOU",
                required=True
            )
