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
        fields = ['user']

    def __init__(self, username, *args, **kwargs):
        super(BookEntryForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(username=username)
        if 'user' in kwargs:
            username = kwargs.pop('user')
            self.fields['user'].initial = "username"