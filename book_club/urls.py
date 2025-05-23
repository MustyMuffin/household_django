from django.urls import path, include
from . import views

app_name = 'book_club'

urlpatterns = [
    # Auth URLs
    path('', include('django.contrib.auth.urls')),

    # Book views
    path('', views.books_by_category, name='books_by_category'),
    path('books/', views.books, name='books'),
    path('books/<int:book_id>/', views.book, name='book'),
    path('book_backlog/', views.book_backlog, name='book_backlog'),

    # Book entries and trackers
    path('new_book_entry/<int:book_id>/', views.new_book_entry, name='new_book_entry'),
    path('new_book_tracker_entry/<int:book_id>/', views.new_book_tracker_entry, name='new_book_tracker_entry'),
    path('update_book_tracker_entry/<int:pk>/', views.update_book_tracker_entry, name='update_book_tracker_entry'),

    # Add new book (Privileged users only)
    path('add_new_book/', views.add_new_book, name='add_new_book'),
]
