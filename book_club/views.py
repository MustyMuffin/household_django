import json
import re
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from book_club.utils import update_badges_for_books
from .api.api_combined import fetch_all_metadata_options
from .forms import BookEntryForm, BookProgressTrackerForm
from .models import Book, BookProgressTracker, BookCategory, BooksRead, BookSeries, BookMetadata
from .utils import calculate_reading_times


def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

def clean_unicode_escapes(text):
    """Clean Unicode escape sequences from text."""
    if not text:
        return text
    try:
        return text.encode('utf-8').decode('unicode-escape')
    except:
        return text

@login_required
def book_title_search(request, book_id=None):
    query = request.GET.get("query", "").strip()
    edit_book = get_object_or_404(Book, id=book_id) if book_id else None

    # print("Debug: edit_book_id", book_id)

    context = {
        "query": query,
        "sources": {},  # To be populated later
        "edit_book_id": edit_book.id if edit_book else "",
        "edit_mode": bool(edit_book),
        "edit_book_title": edit_book.title if edit_book else "",
    }

    return render(request, "book_club/book_title_search.html", context)

from .utils import estimate_word_count_from_pages  # or wherever it’s defined

@login_required
def select_metadata_option(request):
    if request.method == "POST":
        selected_data = json.loads(request.POST.get("selected_data", "{}"))
        edit_book_id = request.POST.get("edit_book_id")
        cover_url = request.POST.get("cover_url")

        pages = selected_data.get("pages") or 0
        try:
            pages = int(pages)
        except (ValueError, TypeError):
            pages = 0


        word_estimate = estimate_word_count_from_pages(pages)

        # Store selected metadata in session
        request.session['prefill_book_data'] = {
            "title": selected_data.get("title", ""),
            "authors": selected_data.get("authors", []),
            "description": selected_data.get("description", "").encode().decode('unicode_escape'),
            "cover_url": selected_data.get("thumbnail_url", "").encode().decode('unicode_escape'),
            "pages": pages,
            "words": word_estimate,
            "source": selected_data.get("source", "manual"),
        }

        if edit_book_id:
            request.session['prefill_book_data']['edit_book_id'] = edit_book_id
            return redirect("book_club:book_edit", book_id=edit_book_id)

        return redirect("book_club:book_create")

    # GET request: show metadata options
    query = request.GET.get('query', '')
    edit_book_id = request.GET.get('edit_book_id')
    # print("DEBUG edit_book_id in select_metadata_option", edit_book_id)

    sources = {}
    if query:
        sources = fetch_all_metadata_options(query)
        for source, items in sources.items():
            for item in items:
                item["json"] = json.dumps(item)

    return render(request, "book_club/select_metadata.html", {
        "query": query,
        "sources": sources,
        "edit_book_id": edit_book_id,
    })


@login_required
def add_new_book(request, book_id=None):
    book = get_object_or_404(Book, id=book_id) if book_id else None
    edit_mode = bool(book)

    if request.method == "POST":
        # 🔄 Handle form submission
        title = request.POST.get("title", "").strip()
        author = request.POST.get("author", "").strip()
        description = request.POST.get("description", "").strip()
        pages = int(request.POST.get("pages") or 0)
        words = int(request.POST.get("words") or estimate_word_count_from_pages(pages))

        # Handle category, series, cover image
        book_category, book_series, cover_url = process_book_associations(request)

        if book:
            book.title = title
            book.authors = author
            book.pages = pages
            book.words = words
            book.book_category = book_category
            book.series = book_series

            BookMetadata.objects.update_or_create(
                book=book,
                defaults={
                    "source": request.POST.get("source", "manual"),
                    "title": title,
                    "authors": [author] if author else [],
                    "description": description,
                    "thumbnail_url": cover_url,
                    "pages": pages
                }
            )
        else:
            book = Book.objects.create(
                title=title,
                pages=pages,
                words=words,
                book_category=book_category,
                series=book_series,
            )
            BookMetadata.objects.update_or_create(
                book=book,
                defaults={
                    "source": request.POST.get("source", "manual"),
                    "title": title,
                    "authors": [author] if author else [],
                    "description": description,
                    "thumbnail_url": cover_url,
                    "pages": pages
                }
            )

        book.save()
        return redirect("book_club:book_detail", book.id)

    # Prefill logic (GET request)
    prefill_data = request.session.pop("prefill_book_data", {})  # use and clear session

    if book and not prefill_data:
        # Inline logic from prefill_book_form()
        metadata = BookMetadata.objects.filter(book=book).first()
        prefill_data = {
            "edit_book_id": str(book.id),
            "title": book.title,
            "author": ", ".join(metadata.authors) if metadata else "",
            "description": metadata.description if metadata else "",
            "cover_url": metadata.thumbnail_url if metadata else "",
            "pages": metadata.pages if metadata and metadata.pages else book.pages,
            "source": metadata.source if metadata else "manual",
            "book_category": str(book.book_category.id) if book.book_category else "",
            "series_name": str(book.series.id) if book.series else "",
            "new_category_name": "",
            "new_series_name": "",
        }

        # Estimate words if needed
        prefill_data["words"] = estimate_word_count_from_pages(prefill_data["pages"])

    return render(request, "book_club/add_new_book.html", {
        "edit_mode": edit_mode,
        "book_id": book.id if book else "",
        "prefill": prefill_data,
        "categories": BookCategory.objects.all(),
        "series": BookSeries.objects.all(),
    })

def process_book_associations(request):
    # Category
    selected_cat_id = request.POST.get("book_category")
    new_category_name = request.POST.get("new_category_name", "").strip()
    book_category = None

    if selected_cat_id == "new" and new_category_name:
        book_category, _ = BookCategory.objects.get_or_create(name=new_category_name)
    elif selected_cat_id:
        book_category = BookCategory.objects.filter(id=selected_cat_id).first()

    # Series
    selected_series_id = request.POST.get("series_name")
    new_series_name = request.POST.get("new_series_name", "").strip()
    book_series = None

    if selected_series_id == "new" and new_series_name:
        book_series, _ = BookSeries.objects.get_or_create(series_name=new_series_name)
    elif selected_series_id:
        book_series = BookSeries.objects.filter(id=selected_series_id).first()

    # Cover
    cover_url = request.POST.get("cover_url", "")
    cover_file = request.FILES.get("cover_upload")
    if cover_file:
        filename = default_storage.save(f"book_covers/{cover_file.name}", cover_file)
        cover_url = default_storage.url(filename)

    return book_category, book_series, cover_url

def render_book_form(request, prefill=None):
    categories = BookCategory.objects.all().order_by("name")
    series = BookSeries.objects.all().order_by("series_name")

    if prefill:
        pages = prefill.get("pages")
        if pages and not prefill.get("words"):
            prefill["words"] = estimate_word_count_from_pages(pages)

    return render(request, "book_club/add_new_book.html", {
        "categories": categories,
        "series": series,
        "prefill": prefill or {},
    })


def book_detail(request, book_id):
    """Show a single book and all its entries, with external metadata."""
    book = get_object_or_404(Book, id=book_id)
    book_entries = book.bookentry_set.order_by('-date_added')
    metadata = BookMetadata.objects.get(book=book)
    tracker = BookProgressTracker.objects.filter(user=request.user, book_name=book).first()
    has_progress = tracker and tracker.words_completed and tracker.words_completed > 0
    want_to_read = tracker.want_to_read if tracker else False
    series = book.series

    # Fix: Handle books without categories
    category = None
    if book.book_category_id:
        category = get_object_or_404(BookCategory, id=book.book_category_id)

    finished_books = BooksRead.objects.filter(user=request.user)
    # print("DEBUG = finished_books = ", finished_books)

    context = {
        'book': book,
        'book_entries': book_entries,
        'metadata': metadata,
        "tracker": tracker,
        "has_progress": has_progress,
        'want_to_read': want_to_read,
        "finished_books": finished_books,
        "series": series,
        "category": category,  # This can now be None
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
    # print("DEBUG = finished_books = ", finished_books)

    return render(request, 'book_club/book_backlog.html', {
        'in_progress_books': in_progress_books,
        'reading_times': reading_times,
        'want_to_read_books': want_to_read_books,
        'finished_books': finished_books,
    })

@login_required
def toggle_want_to_read(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    tracker, created = BookProgressTracker.objects.get_or_create(user=request.user, book_name=book)
    tracker.want_to_read = not tracker.want_to_read
    tracker.save()

    return redirect('book_club:book_detail', book_id=book.id)

@require_POST
def store_and_redirect(request):
    """Store book data in session and redirect to either add or update a book."""

    # Clean all text fields
    title = clean_unicode_escapes(request.POST.get('title', ''))
    description = clean_unicode_escapes(request.POST.get('description', ''))
    cover_url = clean_unicode_escapes(request.POST.get('cover_url', ''))

    # Additional cleaning for description
    if description:
        description = strip_tags(description)
        description = re.sub(r'\s+', ' ', description).strip()

    edit_book_id = request.POST.get('edit_book_id', '')

    # Store all the book data in session
    request.session['prefill_book_data'] = {
        'title': title,
        'author': request.POST.get('author', ''),
        'authors': request.POST.get('author', '').split(', '),
        'description': description,
        'cover_url': cover_url,
        'pages': request.POST.get('pages', ''),
        'source': request.POST.get('source', ''),
        'edit_book_id': edit_book_id,
    }
    # print("Debug: edit_book_id", edit_book_id)

    # 🧠 Redirect based on intent
    if edit_book_id:
        return redirect('book_club:finalize_edit_metadata', book_id=edit_book_id)
    else:
        return redirect('book_club:add_new_book')