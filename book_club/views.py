from collections import defaultdict
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import UserStats, XPLog

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
    """Add a new entry for a book."""
    book = Book.objects.get(id=book_id)

    if request.method != 'POST':
        form = BookEntryForm()
    else:
        form = BookEntryForm(request.POST)
        if form.is_valid():
            new_book_entry = form.save(commit=False)
            new_book_entry.book = book
            new_book_entry.user = request.user
            new_book_entry.save()

            # Update PagesRead/WordsRead if needed (your project already does this)

            # Update XP
            userstats, created = UserStats.objects.get_or_create(user=request.user)
            previous_level = userstats.level

            # Calculate XP earned (example: 1 XP per 10 words)
            xp_earned = int(book.words * 10)  # If you renamed to `words`, adjust this line!

            userstats.xp += xp_earned
            userstats.update_level()

            # Log XP
            XPLog.objects.create(user=request.user, amount=xp_earned, reason=f"Logged book: {book.text}")

            messages.success(request, f"✅ You earned {xp_earned} XP for logging a book!")

            if userstats.level > previous_level:
                messages.success(request, f"🎉 Congratulations! You leveled up to Level {userstats.level}!")

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