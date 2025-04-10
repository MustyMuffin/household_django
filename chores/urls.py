from django.urls import path, include

from . import views

app_name = 'chores'
urlpatterns = [
    # Include default auth urls.
    path('', include('django.contrib.auth.urls')),
    # Chores overall page.
    path('chores/', views.chores, name='chores'),
    # Detail page for a single chore.
    path('chores/<int:chore_id>/', views.chore, name='chore'),
    # # # Page for adding a new chore.
    # path('new_chore/', views.new_chore, name='new_chore'),
    # Page for adding a new entry.
    path('new_chore_entry/<int:chore_id>/', views.new_chore_entry, name='new_chore_entry'),
    # Page for editing an entry.
    # path('edit_chore_entry/<int:chore_entry_id>/', views.edit_chore_entry, name='edit_chore_entry'),
]