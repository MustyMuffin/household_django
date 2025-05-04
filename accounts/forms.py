from django import forms
from .models import Badge
from .constants import ALLOWED_APPS
from django import forms
from accounts.models import Badge

try:
    from chores.models import Chore
except ImportError:
    Chore = None
    print("DEBUG: Chore not imported")

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

        print(f"[DEBUG] BadgeMilestoneForm initialized")

        app = (
                self.data.get("app_label")
                or self.initial.get("app_label")
                or getattr(self.instance, "app_label", None)
        )

        if app == 'chores':
            print("[DEBUG] Using ModelChoiceField for Chores")

            self.fields['milestone_type'] = forms.ModelChoiceField(
                queryset=Chore.objects.all(),
                label='Chore Milestone',
                help_text="Select the specific chore this badge applies to.",
                required=True
            )

        elif app == 'book_club':
            print("[DEBUG] Switching to Book milestone options")

            self.fields['milestone_type'] = forms.ChoiceField(
                choices=[
                    ('books_read', 'Books Read'),
                    ('words_read', 'Words Read'),
                    ('specific_book', 'Specific Book'),
                ],
                label='Book Milestone Type',
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

