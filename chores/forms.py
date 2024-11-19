from django import forms
from django.contrib.auth.models import User

from .models import Chore, ChoreEntry
# from . import views


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['text']
        labels = {'text': ''}

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = ['user']
        
    def __init__(self, username, *args, **kwargs):
        super(ChoreEntryForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(username=username)
        if 'user' in kwargs:
            username = kwargs.pop('user')
            self.fields['user'].initial = "username"

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        # self.fields['user'].queryset = ChoreEntryForm.objects.filter(user=kwargs['request'].user)