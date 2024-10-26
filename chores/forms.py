from django import forms
from django.contrib.auth.models import User

from .models import Chores, ChoreEntry
# from . import views


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chores
        fields = ['text']
        labels = {'text': ''}

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = ['user',]
        
    def __init__(self, username, *args, **kwargs):
        super(ChoreEntryForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(username=username)
        # form.fields["user"].queryset = User.objects.filter(user_id=user.id)
        # if 'user' in kwargs:
        #     user = kwargs.pop('user')
        #     self.fields['user'].initial = user

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        # self.fields['user'].queryset = ChoreEntryForm.objects.filter(user=kwargs['request'].user)