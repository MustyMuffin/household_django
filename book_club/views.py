from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# from django.http import Http404

from .models import Book, BookEntry
from .forms import BookEntryForm

def books(request):
    """Show all Books."""
    books = Book.objects.order_by('text')
    context = {'books': books}
    return render(request, 'book_club/books.html', context)

def book(request, book_id):
    """Show a single chore and all its entries."""
    book = Book.objects.get(id=book_id)
    book_entries = book.bookentry_set.order_by('-date_added')
    context = {'book': book, 'book_entries': book_entries}
    return render(request, 'book_club/book.html', context)

@login_required
def new_book_entry(request, book_id):
    """Add a new entry for a chore."""
    book = Book.objects.get(id=book_id)

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = BookEntryForm(data=request.POST)
    else:
        # POST data submitted; process data.
        form = BookEntryForm(data=request.POST)
        if form.is_valid():
            new_book_entry = form.save(commit=False)
            new_book_entry.book = book
            new_book_entry.user = request.user
            new_book_entry.save()
            return redirect('book_club:book', book_id=book_id)

    # Display a blank or invalid form.
    context = {'book': book, 'form': form}
    return render(request, 'book_club/new_book_entry.html', context)

def new_book(request):
    """Add a new book."""
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = BookForm()
    else:
        # POST data submitted; process data
        form = BookForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/books')

        # Display a blank or invalid form.
        context = {'form': form}
        return render(request, 'book_club/new_book.html', context)