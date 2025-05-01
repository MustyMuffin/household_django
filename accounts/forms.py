from django import forms
from .models import Badge
from chores.models import Chore
from .constants import ALLOWED_APPS
from django import forms
from accounts.models import Badge

try:
    from chores.models import Chore
except ImportError:
    Chore = None

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

        app = (
                self.data.get("app_label")
                or self.initial.get("app_label")
                or getattr(self.instance, "app_label", None)
        )

        print(f"[DEBUG] BadgeMilestoneForm initialized with app_label={app}")

        if 'milestone_type' in self.fields:
            del self.fields['milestone_type']

        if app == 'chores':
            print("[DEBUG] Using ModelChoiceField for Chores")
            self.fields['milestone_type'] = forms.ModelChoiceField(
                queryset=Chore.objects.all(),
                label='Chore Milestone',
                help_text="Select the specific chore this badge applies to.",
                required=True
            )
        elif app == 'book_club':
            print("[DEBUG] Using CharField for Book Club")
            self.fields['milestone_type'] = forms.CharField(
                max_length=100,
                label='Book Milestone',
                help_text="E.g., number of books read or total words read.",
                required=True
            )
        else:
            print("[DEBUG] Using generic fallback CharField")
            self.fields['milestone_type'] = forms.CharField(
                max_length=100,
                label='Milestone Type',
                help_text="Enter a custom milestone (e.g., 'Tasks Completed')",
                required=True
            )

