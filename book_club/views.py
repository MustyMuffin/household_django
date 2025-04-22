from collections import defaultdict
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from accounts.models import XPLog
# from django.http import Http404

from .models import BookCategory, Book, BookEntry, WordsRead, BooksRead
from .forms import BookEntryForm, BookForm

def books_by_category(request):
    # Group books by their category
    books_by_category = defaultdict(list)

    all_books = Book.objects.all()

    for item in all_books:
        category_name = item.book_category.name if item.book_category else "Uncategorized"
        books_by_category[category_name].append(item)

    print("Categories in view context:", books_by_category.keys())

    context = {'books_by_category': dict(books_by_category)}
    return render(request, 'book_club/books_by_category.html', context)

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
    """Add a new entry for a book read and track pages read."""
    book = Book.objects.get(id=book_id)

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = BookEntryForm()
    else:
        # POST data submitted; process data.
        form = BookEntryForm(data=request.POST)
        if form.is_valid():
            new_book_entry = form.save(commit=False)
            new_book_entry.book = book
            new_book_entry.user = request.user
            new_book_entry.save()

            # Always create a new BooksRead entry
            BooksRead.objects.create(
                user=request.user,
                book_name=book.text
            )

            # Update cumulative page count in PagesRead
            words_read_entry, created = WordsRead.objects.get_or_create(
                user=request.user,
                defaults={'wordsLifetime': 0}
            )
            words_read_entry.wordsLifetime += book.words
            words_read_entry.save()

            # Get last XP log entry for this user (just created in signal)
            xp_awarded = XPLog.objects.filter(user=request.user).order_by('-date_awarded').first()
            if xp_awarded:
                messages.success(request, f"You earned {xp_awarded.amount} XP for logging a book!")

            return redirect('book_club:books_by_category')

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