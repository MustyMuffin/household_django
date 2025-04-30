from django.urls import path, include
from accounts.views import activity_feed
from . import views
from .admin import get_milestone_options

app_name = 'accounts'

urlpatterns = [
 # Include default auth urls.
 path('', include('django.contrib.auth.urls')),
 # Registration page.
 path('register/', views.register, name='register'),
 path('profile/<str:username>/', views.user_profile, name='user_profile'),
 path('activity_feed/', activity_feed, name='activity_feed'),
 path('badges/', views.all_badges, name='all_badges'),
 path("admin/badges/milestone-options/", get_milestone_options, name="badge_milestone_options"),
]