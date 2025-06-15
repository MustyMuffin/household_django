from django import forms
from django.contrib.auth.models import User
from decimal import Decimal

from django.forms.widgets import DateTimeInput
from django.utils import timezone

from .models import Chore, ChoreEntry, EarnedWage, ChoreCategory

# from . import views

class ChoreForm(forms.ModelForm):
    selected_cat_id = forms.ChoiceField(label="Category", required=False)
    new_category_name = forms.CharField(
        max_length=100, required=False,
        label="Or enter a new category",
        help_text="Leave blank if choosing an existing category"
    )

    class Meta:
        model = Chore
        fields = ['name', 'wage']  # exclude category from model fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = ChoreCategory.objects.all()
        choices = [("", "--- Select a category ---")]
        choices += [(cat.id, cat.name) for cat in categories]
        choices.append(("new", "➕ New Category"))
        self.fields["selected_cat_id"].choices = choices

class ChoreEntryForm(forms.ModelForm):
    class Meta:
        model = ChoreEntry
        fields = []


class ChoreEntryEditForm(forms.ModelForm):
    """Form for editing chore entry with timezone-aware datetime field."""

    date_added = forms.DateTimeField(
        widget=DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }
        ),
        help_text="Date and time when the chore was completed",
        label="Completion Date & Time"
    )

    class Meta:
        model = ChoreEntry  # Adjust based on your model name
        fields = ['date_added']  # Only include editable fields
        widgets = {
            'date_added': DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert timezone-aware datetime to local datetime for the widget
        if self.instance and self.instance.date_added:
            # Convert to user's local timezone for display
            local_dt = timezone.localtime(self.instance.date_added)
            # Format for datetime-local input (remove timezone info)
            self.initial['date_added'] = local_dt.strftime('%Y-%m-%dT%H:%M')


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