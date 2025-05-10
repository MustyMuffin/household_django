from collections import defaultdict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from book_club.utils import update_badges_for_books
from accounts.badge_helpers import check_and_award_badges
from accounts.xp_helpers import award_xp
from .forms import BookEntryForm, BookForm, BookProgressTrackerForm
from .models import Book, WordsRead, BookProgressTracker

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
            try:
                tracker = BookProgressTracker.objects.get(user=request.user, book_name=book)
                remaining_words = max(book.words - tracker.words_completed, 0)
                tracker.delete()
                print(f"[DEBUG] Tracker found. Awarding {remaining_words} words worth of XP.")
                result = award_xp(
                    user=request.user,
                    source_object=remaining_words,
                    reason="📚 Finished tracked book",
                    source_type="book_partial"
                )
            except BookProgressTracker.DoesNotExist:
                print(f"[DEBUG] No tracker found. Awarding full {book.words} words.")
                result = award_xp(
                    user=request.user,
                    source_object=book,
                    reason=f"Logged book: {book.text}",
                    source_type="book"
                )

            # Save the final entry
            new_entry = form.save(commit=False)
            new_entry.book = book
            new_entry.user = request.user
            new_entry.save()

            # Award bonus for finishing
            result = award_xp(
                user=request.user,
                source_object=book,
                reason="📚 Finished full book bonus",
                source_type="finished_book"
            )

            if result.get('xp_awarded', 0) > 0:
                messages.success(request, f"✅ Bonus XP: {result['xp_awarded']} for finishing a book!")

            if result.get('leveled_up'):
                messages.success(request, f"🎉 You leveled up to Level {result['new_level']}!")

            # 🔁 REPLACEMENT: Badge + stats update
            update_badges_for_books(
                user=request.user,
                book=book,
                words_increment=book.words,
                request=request
            )

            return redirect('book_club:books_by_category')

    context = {'book': book, 'form': form}
    return render(request, 'book_club/new_book_entry.html', context)


@login_required()
def new_book_tracker_entry(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # Check for existing entry
    existing_entry = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()

    if existing_entry and request.method != 'POST':
        messages.warning(request, f"You've already logged progress for this book. Update your previous entry.")
        return redirect('book_club:update_book_tracker_entry', pk=existing_entry.pk)

    form = BookProgressTrackerForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        words_progress = form.cleaned_data['words_completed']
        words_progress_int = int(words_progress)

        new_entry = form.save(commit=False)
        new_entry.book_name = book
        new_entry.user = request.user
        new_entry.words_completed = words_progress_int
        new_entry.save()

        words_entry, _ = WordsRead.objects.get_or_create(user=new_entry.user)
        words_entry.wordsLifetime += words_progress_int
        words_entry.save()

        result = award_xp(
            user=request.user,
            source_object=words_progress_int,
            reason=f"📘 Logged partial progress in '{book.text}'",
            source_type="book_partial"
        )

        if result.get('xp_awarded', 0) > 0:
            messages.success(request, f"✅ You earned {result['xp_awarded']} XP for logging progress.")

        if result.get('leveled_up'):
            messages.success(request, f"🎉 You leveled up to Level {result['new_level']}!")

        update_badges_for_books(
            user=request.user,
            book=book,
            words_increment=words_progress_int,
            request=request
        )

        return redirect('book_club:books_by_category')

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
            new_words_completed = form.cleaned_data['words_completed']
            words_progressed = new_words_completed - old_words_completed

            words_entry, _ = WordsRead.objects.get_or_create(user=entry.user)
            words_entry.wordsLifetime += words_progressed
            words_entry.save()

            messages.success(request, f"✅ Updated progress for '{book}'")

            result = award_xp(
                user=request.user,
                source_object=words_progressed,
                reason=f"📘 Updated progress for '{book.text}'",
                source_type="book_partial"
            )

            if result.get('xp_awarded', 0) > 0:
                messages.success(request, f"✅ You earned {result['xp_awarded']} XP for additional progress.")

            if result.get('leveled_up'):
                messages.success(request, f"🎉 You leveled up to Level {result['new_level']}!")

            update_badges_for_books(
                user=request.user,
                book=book,
                words_increment=words_progressed,
                request=request
            )

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