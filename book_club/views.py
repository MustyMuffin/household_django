from collections import defaultdict
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from book_club.utils import update_badges_for_books
from accounts.badge_helpers import check_and_award_badges
from accounts.xp_helpers import award_xp
from .forms import BookEntryForm, BookForm, BookProgressTrackerForm
from .models import Book, BookProgressTracker, BookCategory
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

    context = {
        'book': book,
        'book_entries': book_entries,
        'metadata': metadata,
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
def new_book_tracker_entry(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    existing_entry = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()

    if existing_entry and request.method != 'POST':
        messages.warning(request, "You've already logged progress for this book.")
        return redirect('book_club:update_book_tracker_entry', pk=existing_entry.pk)

    form = BookProgressTrackerForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        words = int(form.cleaned_data['words_completed'])

        form.instance.book_name = book
        form.instance.user = request.user
        form.instance.words_completed = words
        form.save()

        log_words(request.user, words, book, request)
        return redirect('book_club:books_by_category')

    return render(request, 'book_club/new_book_tracker_entry.html', {'form': form, 'book': book})


@login_required
def update_book_tracker_entry(request, pk):
    entry = get_object_or_404(BookProgressTracker, pk=pk, user=request.user)
    book = entry.book_name
    old_words = entry.words_completed

    form = BookProgressTrackerForm(request.POST or None, instance=entry)

    if request.method == 'POST' and form.is_valid():
        new_words = form.cleaned_data['words_completed']
        progress = new_words - old_words
        form.save()

        if progress > 0:
            log_words(request.user, progress, book, request)

        messages.success(request, f"✅ Updated progress for '{book}'")
        return redirect('book_club:books_by_category')

    return render(request, 'book_club/update_book_tracker_entry.html', {'form': form, 'book': book})


@login_required
def book_backlog(request):
    in_progress_books = BookProgressTracker.objects.select_related('book_name').filter(
        user=request.user,
        words_completed__gt=0,
    ).exclude(words_completed__gte=F('book_name__words'))

    reading_times = {}

    for entry in in_progress_books:
        result = calculate_reading_times(request.user, entry.book_name, words_completed=entry.words_completed)
        if isinstance(result, dict) and "total_minutes" in result:
            reading_times[entry.book_name.id] = result

    return render(request, 'book_club/book_backlog.html', {
        'in_progress_books': in_progress_books,
        'reading_times': reading_times
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

        if selected_cat_id == "new" and new_category_name:
            book_category, _ = BookCategory.objects.get_or_create(name=new_category_name)
        elif selected_cat_id:
            book_category = BookCategory.objects.filter(id=selected_cat_id).first()

        # ✅ Create and save the book
        book = Book.objects.create(
            title=title,
            words=word_count,
            book_category=book_category,
        )

        # ✅ Attach external metadata
        fetch_and_cache_metadata(book)

        return redirect("book_club:book_detail", book_id=book.id)

    # GET request: show empty form
    categories = BookCategory.objects.all().order_by("name")
    return render(request, "book_club/add_new_book.html", {
        "categories": categories,
    })

