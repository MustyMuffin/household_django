from collections import defaultdict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from .forms import BookEntryForm, BookForm, BookProgressTrackerForm
from .models import Book, WordsRead, BooksRead, BookProgressTracker


def books_by_category(request):
    # Group books by their category
    books_by_category = defaultdict(list)

    all_books = Book.objects.all()

    for item in all_books:
        category_name = item.book_category.name if item.book_category else "Uncategorized"
        books_by_category[category_name].append(item)

    context = {'books_by_category': dict(books_by_category)}
    return render(request, 'book_club/books_by_category.html', context)

def books(request):
    """Show all Books."""
    books = Book.objects.order_by('text')
    context = {'books': books}
    return render(request, 'book_club/books.html', context)

def book(request, book_id):
    """Show a single book and all its entries."""
    book = Book.objects.get(id=book_id)
    book_entries = book.bookentry_set.order_by('-date_added')
    context = {'book': book, 'book_entries': book_entries}
    return render(request, 'book_club/book.html', context)

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

            books_read_record, created = BooksRead.objects.get_or_create(
                user=request.user,
                book_name=book.text
            )

            from accounts.badge_helpers import check_and_award_badges

            # Count total books read
            books_read_total = BooksRead.objects.filter(user=request.user).count()
            # print(f"DEBUG: Books read total for this user: {books_read_total}")

            # Check for book-related badges
            check_and_award_badges(
                user=request.user,
                app_label="book_club",
                milestone_type="books_read",
                current_value=books_read_total,
                request=request
            )

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

            words_total = WordsRead.objects.get(user=request.user).wordsLifetime

            check_and_award_badges(
                user=request.user,
                app_label="book_club",
                milestone_type="words_read",
                current_value=words_total,
                request=request
            )

            userstats, _ = UserStats.objects.get_or_create(user=request.user)
            if hasattr(userstats, 'words_read'):
                userstats.words_read += book.words
                userstats.save(update_fields=["words_read"])

            return redirect('book_club:books_by_category')

    context = {'book': book, 'form': form}
    return render(request, 'book_club/new_book_entry.html', context)

@login_required()
def new_book_tracker_entry(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # Check for existing entry
    existing_entry = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()

    if existing_entry and request.method != 'POST':
        # Prompt the user to confirm update
        messages.warning(request, f"You've already logged progress for this book. Would you like to update your entry?")
        return redirect('book_club:update_book_tracker_entry', pk=existing_entry.pk)

    form = BookProgressTrackerForm(request.POST or None)

    if request.method == 'POST':
        form = BookProgressTrackerForm(request.POST)
        if form.is_valid():
            words_progress = form.cleaned_data['words_completed']
            words_progress_int = int(words_progress)

            new_entry = form.save(commit=False)
            new_entry.book_name = book
            new_entry.user = request.user
            new_entry.words_completed = words_progress_int
            new_entry.save()

            words_entry, created = WordsRead.objects.get_or_create(user=request.user)
            words_entry.wordsLifetime += words_progress_int
            words_entry.save()

            result = award_xp(
                user=request.user,
                source_object=words_progress_int,
                reason=f"Logged book: {book.text}",
                source_type="book_partial"
            )

            if result.get('xp_awarded', 0) > 0:
                messages.success(request, f"✅ You earned {result['xp_awarded']} XP for logging a book!")

            if result.get('leveled_up'):
                messages.success(request, f"🎉 Congratulations! You leveled up to Level {result['new_level']}!")

            words_total = WordsRead.objects.get(user=request.user).wordsLifetime

            userstats, _ = UserStats.objects.get_or_create(user=request.user)
            if hasattr(userstats, 'words_read'):
                userstats.words_read += book.words
                userstats.save(update_fields=["words_read"])

            return redirect('book_club:books_by_category')
    else:
        form = BookProgressTrackerForm()

    return render(request, 'book_club/new_book_tracker_entry.html', {
        'form': form,
        'book': book
    })


@login_required
def update_book_tracker_entry(request, pk):
    entry = get_object_or_404(BookProgressTracker, pk=pk, user=request.user)
    book = entry.book_name
    old_words_completed = entry.words_completed

    if request.method == 'POST':
        form = BookProgressTrackerForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Updated progress for '{book}'")
            new_words_completed = form.cleaned_data['words_completed']
            words_progressed = new_words_completed - old_words_completed

            result = award_xp(
                user=request.user,
                source_object=words_progressed,
                reason=f"Logged book: {book.text}",
                source_type="book_partial"
            )

            if result.get('xp_awarded', 0) > 0:
                messages.success(request, f"✅ You earned {result['xp_awarded']} XP for logging a book!")

            if result.get('leveled_up'):
                messages.success(request, f"🎉 Congratulations! You leveled up to Level {result['new_level']}!")

            words_total = WordsRead.objects.get(user=request.user).wordsLifetime

            userstats, _ = UserStats.objects.get_or_create(user=request.user)
            if hasattr(userstats, 'words_read'):
                userstats.words_read += book.words
                userstats.save(update_fields=["words_read"])

            return redirect('book_club:books_by_category')

    else:
        form = BookProgressTrackerForm(instance=entry)

    return render(request, 'book_club/update_book_tracker_entry.html', {
        'form': form,
        'book': book
    })

@login_required
def book_backlog(request):
    in_progress_books = BookProgressTracker.objects.select_related('book_name').filter(
        user=request.user,
        words_completed__gt=0,
    ).exclude(words_completed__gte=F('book_name__words'))

    return render(request, 'book_club/book_backlog.html', {
        'in_progress_books': in_progress_books
    })


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