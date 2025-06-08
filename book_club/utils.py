from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from .models import BooksRead, BookProgressTracker, Book
from math import ceil

def update_badges_for_books(user, book, words_increment, request=None):
    # Only count as "read" if full progress is met
    tracker = BookProgressTracker.objects.filter(user=user, book_name=book).first()
    if tracker and tracker.words_completed < book.words:
        return

    BooksRead.objects.get_or_create(user=user, book_name=book.title)

    books_read_total = BooksRead.objects.filter(user=user).count()

    words_total = UserStats.objects.filter(user=user).first().words_read

    check_and_award_badges(
        user=user,
        app_label="book_club",
        milestone_type="books_read",
        current_value=books_read_total,
        request=request
    )
    check_and_award_badges(
        user=user,
        app_label="book_club",
        milestone_type="words_read",
        current_value=words_total,
        request=request
    )

    userstats, _ = UserStats.objects.get_or_create(user=user)
    userstats.words_read += words_increment
    userstats.save(update_fields=["words_read"])


def calculate_reading_times(user, book, words_completed=0):
    try:
        user_stats = UserStats.objects.get(user=user)
    except UserStats.DoesNotExist:
        return {"error": "UserStats not found"}

    if not user_stats.reading_wpm or user_stats.reading_wpm <= 0:
        return {"error": "Invalid reading WPM"}

    total_words = book.words or 0
    remaining_words = max(0, total_words - words_completed)

    total_minutes = total_words / user_stats.reading_wpm
    remaining_minutes = remaining_words / user_stats.reading_wpm

    def format_time(minutes):
        hours = int(minutes) // 60
        mins = int(minutes) % 60
        return f"{hours}h {mins}m" if hours else f"{mins}m"

    return {
        "total_minutes": round(total_minutes, 2),
        "remaining_minutes": round(remaining_minutes, 2),
        "total_human": format_time(total_minutes),
        "remaining_human": format_time(remaining_minutes),
    }