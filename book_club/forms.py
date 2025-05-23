from django import forms


from .models import Book, BookEntry, BookProgressTracker


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['text', 'words', 'book_category']


class BookEntryForm(forms.ModelForm):
    class Meta:
        model = BookEntry
        fields = []


class BookProgressTrackerForm(forms.ModelForm):
    class Meta:
        model = BookProgressTracker
        fields = ['text', 'words_completed']