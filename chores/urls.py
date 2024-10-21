"""Defines URL patterns for chores."""

from django.urls import path, include

from . import views

app_name = 'chores'
urlpatterns = [
    # Include default auth urls.
    path('', include('django.contrib.auth.urls')),
    # Chores overall page.
    path('chores/', views.chores, name='chores'),
]