"""Defines URL patterns for household_main"""

from django.urls import path

from . import views

app_name = 'household_main'
urlpatterns = [
    # Home Page
    path('', views.index, name='index'),
]