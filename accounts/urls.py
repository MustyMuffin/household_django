from django.urls import path, include
from accounts.views import activity_feed, AllBadges, MilestoneTypeOptionsView
from . import views

app_name = 'accounts'

urlpatterns = [
 # Include default auth urls.
 path('', include('django.contrib.auth.urls')),
 # Registration page.
 path('register/', views.register, name='register'),
 path('profile/edit-picture/', views.edit_profile_picture, name='edit_profile_picture'),
 path('profile/<str:username>/', views.user_profile, name='user_profile'),
 path('activity_feed/', activity_feed, name='activity_feed'),
 path('badges/', AllBadges.as_view(), name='all_badges'),
 path("admin/accounts/badge/milestone_options/", views.get_milestone_options, name='accounts_badge_milestone_options'),
 path("badges/milestone_options/", MilestoneTypeOptionsView.as_view(), name="badge_milestone_options"),
]