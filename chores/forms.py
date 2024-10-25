from django import forms

from .models import Chores, ChoreEntry
# from . import import views


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chores
        fields = ['text']
        labels = {'text': ''}

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = ['user',]
        
    def __init__(self, *args, **kwargs):
        super(ChoreEntryForm, self).__init__(*args, **kwargs)
        if 'user' in kwargs:
            user = kwargs.pop('user')
            self.fields['user'].initial = user