from django import forms
from accounts.models import Badge
from book_club.models import Book
from chores.models import Chore
from gaming.models import Game
from .constants import ALLOWED_APPS
from .models import Badge, UserStats

try:
    from chores.models import Chore
except ImportError:
    Chore = None
    # print("DEBUG: Chore not imported")


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserStats
        fields = ['profile_picture']

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

        app = None

        if "app_label" in self.data:
            app = self.data.get("app_label")
        elif "app_label" in self.initial:
            app = self.initial["app_label"]
        elif hasattr(self.instance, "app_label") and self.instance.app_label:
            app = self.instance.app_label

        if app == 'chores':
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
            self.fields['milestone_type'] = forms.ChoiceField(
                choices=[
                    ('books_read', 'Books Read'),
                    ('words_read', 'Words Read'),
                ],
                label='Book Milestone Type',
                required=True
            )

        elif app == 'gaming':
            from gaming.models import Game  # Ensure this import is present

            base_choices = [
                ('games_beaten', 'Games Beaten'),
                ('hours_played', 'Hours Played'),
            ]

            # Dynamically include all games
            game_choices = [
                (f'game_completion_combo_{game.id}', f'🏆 Full Completion – {game.name}')
                for game in Game.objects.all()
            ]

            combined_choices = base_choices + game_choices

            self.fields['milestone_type'] = forms.ChoiceField(
                choices=combined_choices,
                label='Gaming Milestone Type',
                required=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        milestone_type = cleaned_data.get("milestone_type")
        app_label = cleaned_data.get("app_label")
        game = cleaned_data.get("game")

        if app_label == "gaming" and milestone_type == "game_completion_combo" and not game:
            self.add_error("game", "You must select a game for this type of badge.")




