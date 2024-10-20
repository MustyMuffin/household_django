"""Defines URL patterns for household_main"""

from django.urls import path

from . import views

app_name = 'household_main'
urlpatterns = [
    # Home Page
    path('', views.index, name='index'),
    # Page that shows all notes.
    path('notes/', views.notes, name='notes'),
    # Detail page for a single topic.
    path('notes/<int:note_id>/', views.note, name='note'),

]