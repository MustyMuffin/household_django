"""Defines URL patterns for household_main"""

from django.urls import path

from . import views

app_name = 'household_main'
urlpatterns = [
    # Home Page
    path('', views.index, name='index'),
    # Page that shows all notes.
    path('notes/', views.notes, name='notes'),
    # Detail page for a single note.
    path('notes/<int:note_id>/', views.note, name='note'),
    # Page for adding a new note.
    path('new_note/', views.new_note, name='new_note'),
    # Page for adding a new entry.
     path('new_entry/<int:note_id>/', views.new_entry, name='new_entry'),
    # Page for editing an entry.
    path('edit_entry/<int:entry_id>/', views.edit_entry, name='edit_entry'),
]