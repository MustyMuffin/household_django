from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import UserStats
from .forms import BookEntryForm, BookForm
from .models import Book, WordsRead


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

from accounts.xp_helpers import award_xp  # import central XP awarder

@login_required
def new_book_entry(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method != 'POST':
        form = BookEntryForm()
    else:
        form = BookEntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.book = book
            new_entry.user = request.user
            new_entry.save()


            # Award XP using the xp helper
            result = award_xp(
                user=request.user,
                source_object=book,
                reason=f"Logged book: {book.text}",
                source_type="book"
            )

            if result.get('xp_awarded', 0) > 0:
                messages.success(request, f"✅ You earned {result['xp_awarded']} XP for logging a book!")

            if result.get('leveled_up'):
                messages.success(request, f"🎉 Congratulations! You leveled up to Level {result['new_level']}!")

            words_entry, created = WordsRead.objects.get_or_create(user=request.user)
            words_entry.wordsLifetime += book.words
            words_entry.save()

            # Update UserStats (total words if you track it here too)
            userstats, _ = UserStats.objects.get_or_create(user=request.user)
            if hasattr(userstats, 'words_read'):
                userstats.words_read += book.words
                userstats.save(update_fields=["words_read"])

            return redirect('book_club:books_by_category')

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