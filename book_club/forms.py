from django import forms


from .models import Book, BookEntry, BookProgressTracker


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['text']
        labels = {'text': ''}


class BookEntryForm(forms.ModelForm):
    class Meta:
        model = BookEntry
        fields = []


class BookProgressTrackerForm(forms.ModelForm):
    class Meta:
        model = BookProgressTracker  # or your custom model
        fields = ['text', 'words_completed']


# class BookProgressTrackerForm(forms.ModelForm):
#     class Meta:
#         model = BookProgressTracker
#         fields = ['text', 'words_completed']
#         labels = {'text': '', 'words_completed': ''}

# class BookProgressTrackerForm(forms.Form):
#     words_completed = forms.IntegerField(widget=forms.HiddenInput())
#     notes = forms.CharField(widget=forms.Textarea, required=False)