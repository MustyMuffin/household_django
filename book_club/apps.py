from django.apps import AppConfig

class BookClubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'book_club'

    def ready(self):
        import book_club.signals
        import book_club.badge_progress_book_club