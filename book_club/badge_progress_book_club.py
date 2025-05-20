from book_club.models import BooksRead
from accounts.models import UserStats
from accounts.badge_helpers import BadgeProgressProvider

@BadgeProgressProvider.register("book_club")
def get_books_progress(badge, user):
    count = BooksRead.objects.filter(user=user).count()
    return min(int((count / badge.milestone_value) * 100), 100)

@BadgeProgressProvider.register("book_club")
def get_words_read_progress(badge, user):
    try:
        count = UserStats.objects.get(user=user).words_read
        return min(int((count / badge.milestone_value) * 100), 100)
    except UserStats.DoesNotExist:
        return 0
