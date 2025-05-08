from book_club.models import BooksRead, WordsRead
from accounts.badge_helpers import BadgeProgressProvider

@BadgeProgressProvider.register("book_club")
def get_books_progress(badge, user):
    count = BooksRead.objects.filter(user=user).count()
    return min(int((count / badge.milestone_value) * 100), 100)

@BadgeProgressProvider.register("book_club")
def get_words_read_progress(badge, user):
    try:
        count = WordsRead.objects.get(user=user).wordsLifetime
        return min(int((count / badge.milestone_value) * 100), 100)
    except WordsRead.DoesNotExist:
        return 0
