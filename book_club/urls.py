from django.urls import path, include
from . import views

from .api.api_googlebooks import fetch_google_volume_detail

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

    # Book metadata search + APIs
    path("books/search/", views.book_title_search, name="book_search"),
    path("books/search/<int:book_id>/", views.book_title_search, name="book_search_with_id"),
    path("books/metadata/options/", views.select_metadata_option, name="select_metadata"),
    path('api/fetch_google_volume/<str:volume_id>/', fetch_google_volume_detail, name='fetch_google_volume_detail'),

    # Book CRUD
    path("render_book_form/<int:book_id>/", views.render_book_form, name="render_book_form"),
    path("books/add/", views.add_new_book, name="book_create"),
    path("books/edit/<int:book_id>/", views.add_new_book, name="book_edit"),


]
