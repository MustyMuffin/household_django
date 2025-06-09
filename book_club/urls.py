from django.urls import path, include
from . import views

app_name = 'book_club'

urlpatterns = [
    # Auth URLs
    path('', include('django.contrib.auth.urls')),
    # Book views
    path('', views.books_by_category, name='books_by_category'),
    path('books/', views.books, name='books'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book_backlog/', views.book_backlog, name='book_backlog'),

    # Book entries and trackers
    path('new_book_entry/<int:book_id>/', views.new_book_entry, name='new_book_entry'),
    path('book/track/<int:book_id>/', views.book_tracker_entry, name='new_book_tracker_entry'),
    path('book/update/<int:pk>/', views.book_tracker_entry, name='update_book_tracker_entry'),
    path('toggle_want_to_read/<int:book_id>/', views.toggle_want_to_read, name='toggle_want_to_read'),


    # Add new book (Privileged users only)
    path('add_new_book/', views.add_new_book, name='add_new_book'),
    path('api/fetch_book_data/', views.fetch_book_data_api, name='fetch_book_data_api'),
]
