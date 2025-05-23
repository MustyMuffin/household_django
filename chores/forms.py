from django import forms
from django.contrib.auth.models import User
from decimal import Decimal

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

class PartialPayoutForm(forms.Form):
    payout_amount = forms.DecimalField(
        label="Payout Amount",
        min_value=Decimal('0.01'),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 100px;',
            'placeholder': '$0.00',
        })
    )