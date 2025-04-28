from django import forms
from django.contrib.auth.models import User

from .models import Chore, ChoreEntry, EarnedWage

# from . import views

class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['text']
        labels = {'text': ''}

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = []