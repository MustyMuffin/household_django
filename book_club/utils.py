from accounts.badge_helpers import check_and_award_badges
from accounts.models import UserStats
from . models import WordsRead, BooksRead

def update_badges_for_books(user, book=None, words_increment=0, request=None):
    """Handles awarding badges related to books read and words read."""

    # Books Read logic
    if book:
        BooksRead.objects.get_or_create(user=user, book_name=book.text)
        books_read_total = BooksRead.objects.filter(user=user).count()
        check_and_award_badges(
            user=user,
            app_label="book_club",
            milestone_type="books_read",
            current_value=books_read_total,
            request=request
        )

    # Words Read logic
    if words_increment > 0:
        words_entry, _ = WordsRead.objects.get_or_create(user=user)
        words_entry.wordsLifetime += words_increment
        words_entry.save()

        check_and_award_badges(
            user=user,
            app_label="book_club",
            milestone_type="words_read",
            current_value=words_entry.wordsLifetime,
            request=request
        )

        # Update cached user stats for faster dashboard queries
        userstats, _ = UserStats.objects.get_or_create(user=user)
        userstats.words_read += words_increment
        userstats.save(update_fields=["words_read"])
