from django import forms
from .models import Badge
from .constants import ALLOWED_APPS
from django import forms
from accounts.models import Badge

try:
    from chores.models import Chore
except ImportError:
    Chore = None
    # print("DEBUG: Chore not imported")

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

        # print(f"[DEBUG] Fields in form: {list(self.fields.keys())}")
        # print(f"[DEBUG] Form data: {self.data}")
        # print(f"[DEBUG] Form initial: {self.initial}")
        # print(f"[DEBUG] Instance: {self.instance}")
        #
        # print(f"[DEBUG] BadgeMilestoneForm initialized")

        app = None

        # Check POSTed data
        if "app_label" in self.data:
            app = self.data.get("app_label")

        # Check initial data (typically used in change forms)
        elif "app_label" in self.initial:
            app = self.initial["app_label"]

        # Check model instance (if editing an existing Badge)
        elif hasattr(self.instance, "app_label") and self.instance.app_label:
            app = self.instance.app_label

        # print(f"[DEBUG] app: {app}")

        if app == 'chores':
            # print("[DEBUG] Using ChoiceField with wage + chores")

            chore_choices = [(str(chore.id), chore.text) for chore in Chore.objects.all()]
            wage_option = [('earned_wage', 'Total Wage Earned')]
            combined_choices = wage_option + chore_choices

            self.fields['milestone_type'] = forms.ChoiceField(
                choices=combined_choices,
                label='Chore Milestone Type',
                help_text="Select a chore or choose 'Total Wage Earned'.",
                required=True
            )

        elif app == 'book_club':
            # print("[DEBUG] Switching to Book milestone options")

            self.fields['milestone_type'] = forms.ChoiceField(
                choices=[
                    ('books_read', 'Books Read'),
                    ('words_read', 'Words Read'),
                    # ('specific_book', 'Specific Book'),
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



