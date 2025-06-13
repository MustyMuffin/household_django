from django.core.management.base import BaseCommand
from book_club.models import Book
from book_club.api.api_combined import fetch_and_cache_metadata

class Command(BaseCommand):
    help = "Backfills missing BookMetadata for all books"

    def handle(self, *args, **kwargs):
        books = Book.objects.all()
        created = 0
        skipped = 0

        for book in books:
            if hasattr(book, 'metadata'):
                self.stdout.write(f"Skipping: {book.text}")
                skipped += 1
                continue

            metadata = fetch_and_cache_metadata(book)
            if metadata:
                self.stdout.write(self.style.SUCCESS(f"Created metadata for: {book.text}"))
                created += 1
            else:
                self.stdout.write(self.style.WARNING(f"No metadata found for: {book.text}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Done. Created: {created}, Skipped: {skipped}"))
