from django.urls import path, include

from . import views

app_name = 'chores'
urlpatterns = [
    # Include default auth urls.
    path('', include('django.contrib.auth.urls')),
    # Chores overall page.
    path('chores_by_category/', views.chores_by_category, name='chores_by_category'),
    # Detail page for a single chore.
    path('chores/<int:chore_id>/', views.chore, name='chore'),
    # # # Page for adding a new chore.
    path('add_new_chore/', views.add_new_chore, name='add_new_chore'),
    # Page for adding a new entry.
    path('new_chore_entry/<int:chore_id>/', views.new_chore_entry, name='new_chore_entry'),
    path('edit-entry/<int:chore_id>', views.edit_chore_entry, name='edit_chore_entry'),
    path('<int:chore_id>/edit-entry/<int:entry_id>/', views.edit_chore_entry, name='edit_specific_chore_entry'),
    path('edit-entry/<int:entry_id>/', views.edit_chore_entry, name='edit_specific_chore_entry'),
    path('select-entry-to-edit/<int:chore_id>/', views.select_chore_entry_to_edit, name='select_entry_to_edit'),

    # Paths for payout
    path('payout/', views.payout, name='payout'),
    path('reset/<int:user_id>/', views.reset_earned_wage, name='reset_earned_wage'),

    # Paths for Analytics
    path('payout_summary/', views.payout_summary, name='payout_summary'),
    path('payout_partial/<int:user_id>/', views.payout_partial, name='payout_partial'),
    path('analytics/', views.chore_analytics, name='chore_analytics'),
    path("analytics/json/", views.chore_analytics_json, name="chore_analytics_json"),

    # Page for editing an entry.
    # path('edit_chore_entry/<int:chore_entry_id>/', views.edit_chore_entry, name='edit_chore_entry'),
]