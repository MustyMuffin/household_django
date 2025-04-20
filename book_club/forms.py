from django import forms


from .models import Book, BookEntry

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['text']
        labels = {'text': ''}


class BookEntryForm(forms.ModelForm):
    class Meta:
        model = BookEntry
        fields = []