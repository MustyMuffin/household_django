from django import forms


from .models import Game, GameEntry, GameProgressTracker


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name', 'hours', 'game_category']


class GameEntryForm(forms.ModelForm):
    class Meta:
        model = GameEntry
        fields = []


class GameProgressTrackerForm(forms.ModelForm):
    class Meta:
        model = GameProgressTracker
        fields = ['text', 'hours_completed']