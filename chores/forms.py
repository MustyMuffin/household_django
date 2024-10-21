from django import forms

from .models import Chores, ChoreEntry


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chores
        fields = ['text', 'price']
        labels = {'text': '', 'price': ''}

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = ['text']
        labels = {'text': ''}
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}