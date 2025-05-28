from django import forms


from .models import Game, GameEntry, GameProgress


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name', 'game_category']


class GameEntryForm(forms.ModelForm):
    class Meta:
        model = GameEntry
        fields = []


class GameProgressTrackerForm(forms.ModelForm):
    class Meta:
        model = GameProgress
        fields = ['hours_played', 'beaten', 'note']