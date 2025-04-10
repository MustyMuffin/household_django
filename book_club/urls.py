from django.urls import path, include

from . import views

app_name = 'book_club'
urlpatterns = [
    # Home Page
    path('', include('django.contrib.auth.urls')),
    # Page that shows all topics.
    path('books/', views.books, name='books'),
    path('books/<int:id>/', views.book, name='book'),
    path('new_book_entry/<int:book_id>/', views.new_book_entry, name='new_book_entry'),
]