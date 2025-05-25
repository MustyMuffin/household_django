from django.urls import path
from .views import achievements_view

urlpatterns = [
    path('', achievements_view, name='achievements'),
]