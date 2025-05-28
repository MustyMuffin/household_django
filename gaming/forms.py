from django import forms


from .models import Game, GameEntry, GameProgress, CollectibleType


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

class CollectibleTypeForm(forms.ModelForm):
    class Meta:
        model = CollectibleType
        fields = ['name', 'total_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'total_available': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }