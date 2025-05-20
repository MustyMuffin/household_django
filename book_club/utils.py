from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from .models import BooksRead, BookProgressTracker

def update_badges_for_books(user, book, words_increment, request=None):
    # Only count as "read" if full progress is met
    tracker = BookProgressTracker.objects.filter(user=user, book_name=book).first()
    if tracker and tracker.words_completed < book.words:
        return

    BooksRead.objects.get_or_create(user=user, book_name=book.text)

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
