from django import forms
# from django.utils import timezone
# from django.contrib.auth.models import User

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
        fields = ['text']
        labels = {'text': ''}