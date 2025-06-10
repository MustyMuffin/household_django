from collections import defaultdict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from book_club.utils import update_badges_for_books
from accounts.badge_helpers import check_and_award_badges
from accounts.xp_helpers import award_xp
from .forms import BookEntryForm, BookForm, BookProgressTrackerForm
from .models import Book, BookProgressTracker, BookCategory, BooksRead, BookSeries
from accounts.models import UserStats
from django.contrib.auth.decorators import user_passes_test
from .api_combined import fetch_and_cache_metadata
from django.http import JsonResponse
from .api_combined import fetch_external_metadata_by_title
from .utils import calculate_reading_times

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

def fetch_book_data_api(request):
    q = request.GET.get('q')
    if not q:
        return JsonResponse({'error': 'Missing query'}, status=400)

    data = fetch_external_metadata_by_title(q)
    if not data:
        return JsonResponse({'error': 'No book found'}, status=404)

    pages = int(data.get("pages", 0))

    print("pages =", pages)

    # Handle estimated word count from pages (if present)
    try:
        pages = int(data.get("pages", 0))
        estimated_words = pages * 275 if pages > 0 else None
        print("DEBUG = estimated_words = ", estimated_words)
    except (ValueError, TypeError):
        estimated_words = None
        print("DEBUG = estimated_words =", estimated_words)

    # Safely return full response
    return JsonResponse({
        "title": data.get("title", ""),
        "authors": data.get("authors", []),
        "description": data.get("description", ""),
        "thumbnail_url": data.get("thumbnail_url") or data.get("thumbnail") or "",
        "external_url": data.get("external_url", ""),
        "source": data.get("source", ""),
        "pages": int(data.get("pages", 0)),
        "estimated_words": estimated_words,
    })


def book_detail(request, book_id):
    """Show a single book and all its entries, with external metadata."""
    book = get_object_or_404(Book, id=book_id)
    book_entries = book.bookentry_set.order_by('-date_added')
    metadata = fetch_and_cache_metadata(book)
    tracker = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()
    has_progress = tracker and tracker.words_completed and tracker.words_completed > 0
    want_to_read = tracker.want_to_read if tracker else False
    series = book.series
    category_id = book.book_category_id
    category = get_object_or_404(BookCategory, id=category_id)

    finished_books = BooksRead.objects.filter(user=request.user)
    print("DEBUG = finished_books = ", finished_books)

    context = {
        'book': book,
        'book_entries': book_entries,
        'metadata': metadata,
        "tracker": tracker,
        "has_progress": has_progress,
        'want_to_read': want_to_read,
        "finished_books": finished_books,
        "series": series,
        "category": category,
    }
    return render(request, 'book_club/book.html', context)

def books_by_category(request):
    # Group books by their category
    books_by_category = defaultdict(list)

    all_books = Book.objects.all()

    for item in all_books:
        category_name = item.book_category.name if item.book_category else "Uncategorized"
        books_by_category[category_name].append(item)

    context = {'books_by_category': dict(books_by_category), 'can_add_book': is_privileged(request.user)}
    return render(request, 'book_club/books_by_category.html', context)

def books(request):
    """Show all Books."""
    books = Book.objects.order_by('title')
    context = {'books': books}
    return render(request, 'book_club/books.html', context)

def log_words(user, words, book, request):
    words_entry, _ = UserStats.objects.get_or_create(user=user)
    words_entry.words_read += words
    words_entry.save()

    result = award_xp(
        user=user,
        source_object=words,
        reason=f"📘 Progress in '{book.title}'",
        source_type="book_partial",
        request=request,
    )

    if result.get('xp_awarded'):
        messages.success(request, f"✅ You earned {result['xp_awarded']} XP for progress!")

    update_badges_for_books(user=user, book=book, words_increment=words, request=request)


@login_required
def new_book_entry(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    form = BookEntryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        tracker = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()

        if tracker:
            remaining_words = max(book.words - tracker.words_completed, 0)
            tracker.delete()
            log_words(request.user, remaining_words, book, request)
        else:
            award_xp(request.user, source_object=book, reason=f"Logged book: {book.title}", source_type="book", request=request)

        form.instance.book = book
        form.instance.user = request.user
        form.save()

        bonus_result = award_xp(request.user, source_object=book, reason="📚 Completed book bonus", source_type="finished_book", request=request)

        if bonus_result.get('xp_awarded'):
            messages.success(request, f"✅ Bonus XP: {bonus_result['xp_awarded']} for finishing a book!")

        update_badges_for_books(user=request.user, book=book, words_increment=book.words, request=request)

        return redirect('book_club:books_by_category')

    return render(request, 'book_club/new_book_entry.html', {'book': book, 'form': form})


@login_required
def book_tracker_entry(request, book_id=None, pk=None):
    # Determine mode: new or update
    if pk:
        entry = get_object_or_404(BookProgressTracker, pk=pk, user=request.user)
        book = entry.book_name
        form = BookProgressTrackerForm(request.POST or None, instance=entry)
        mode = 'update'
        old_words = entry.words_completed
    else:
        book = get_object_or_404(Book, id=book_id)
        existing_entry = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()
        if existing_entry and request.method != 'POST':
            messages.warning(request, "You've already logged progress for this book.")
            return redirect('book_club:update_book_tracker_entry', pk=existing_entry.pk)
        form = BookProgressTrackerForm(request.POST or None)
        mode = 'new'

    if request.method == 'POST' and form.is_valid():
        words = int(form.cleaned_data['words_completed'])
        if mode == 'new':
            form.instance.book_name = book
            form.instance.user = request.user
            form.instance.words_completed = words
            form.save()
            log_words(request.user, words, book, request)
        else:
            progress = words - old_words
            form.save()
            if progress > 0:
                log_words(request.user, progress, book, request)
            messages.success(request, f"✅ Updated progress for '{book}'")

        return redirect('book_club:books_by_category')

    words_value = (
        form.cleaned_data.get("words_completed")
        if form.is_bound
        else form.initial.get("words_completed", 0)
    )

    return render(request, "book_club/book_tracker_entry.html", {
        "form": form,
        "book": book,
        "mode": mode,
        "words_value": words_value,
    })


@login_required
def book_backlog(request):
    in_progress_books = BookProgressTracker.objects.select_related('book_name').filter(
        user=request.user,
        words_completed__gt=0,
    ).exclude(words_completed__gte=F('book_name__words'))

    want_to_read_books = BookProgressTracker.objects.select_related('book_name').filter(
        user=request.user,
        words_completed=0,
        want_to_read=True
    )

    reading_times = {}

    for entry in in_progress_books:
        result = calculate_reading_times(request.user, entry.book_name, words_completed=entry.words_completed)
        if isinstance(result, dict) and "total_minutes" in result:
            reading_times[entry.book_name.id] = result

    finished_books = BooksRead.objects.filter(user=request.user)
    print("DEBUG = finished_books = ", finished_books)

    return render(request, 'book_club/book_backlog.html', {
        'in_progress_books': in_progress_books,
        'reading_times': reading_times,
        'want_to_read_books': want_to_read_books,
        'finished_books': finished_books,
    })

@user_passes_test(is_privileged)
def add_new_book(request):
    if request.method == "POST":
        # ✅ FIRST get the form values
        title = request.POST.get("title")
        author = request.POST.get("author")
        description = request.POST.get("description", "")
        cover_url = request.POST.get("cover_url", "")
        word_count = int(request.POST.get("words") or 0)
        pages = request.POST.get("pageCount")

        # ✅ THEN check for duplicates
        if Book.objects.filter(title__iexact=title).exists():
            categories = BookCategory.objects.all().order_by("name")
            return render(request, "book_club/add_new_book.html", {
                "categories": categories,
                "error": f'A book titled "{title}" already exists.',
                "prefill": request.POST,
            })

        # ✅ Handle category logic
        selected_cat_id = request.POST.get("book_category")
        new_category_name = request.POST.get("new_category_name", "").strip()
        book_category = None
        print("DEBUG = selected_cat_id = ", selected_cat_id)

        if selected_cat_id == "new" and new_category_name:
            book_category, _ = BookCategory.objects.get_or_create(name=new_category_name)
        elif selected_cat_id:
            book_category = BookCategory.objects.filter(id=selected_cat_id).first()

        # ✅ Handle series logic
        selected_series_id = request.POST.get("series_name")
        new_series_name = request.POST.get("new_series_name", "").strip()
        book_series = None
        print("DEBUG = selected_series_id = ", selected_series_id)
        print("DEBUG = new_series_name = ", new_series_name)

        if selected_series_id == "new" and new_series_name:
            book_series, _ = BookSeries.objects.get_or_create(series_name=new_series_name)
        elif selected_series_id:
            book_series = BookSeries.objects.filter(id=selected_series_id).first()

        # ✅ Create and save the book
        book = Book.objects.create(
            title=title,
            words=word_count,
            book_category=book_category,
            pages = pages,
            series=book_series,
        )

        # ✅ Attach external metadata
        fetch_and_cache_metadata(book)

        return redirect("book_club:book_detail", book_id=book.id)

    # GET request: show empty form
    categories = BookCategory.objects.all().order_by("name")
    series = BookSeries.objects.all().order_by("series_name")
    print(categories)
    print(series)
    return render(request, "book_club/add_new_book.html", {
        "categories": categories,
        "series": series,
    })

@login_required
def toggle_want_to_read(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    tracker, created = BookProgressTracker.objects.get_or_create(user=request.user, book_name=book)
    tracker.want_to_read = not tracker.want_to_read
    tracker.save()

    return redirect('book_club:book_detail', book_id=book.id)
