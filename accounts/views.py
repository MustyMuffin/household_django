from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import UserStats, XPSettings, XPLog
from book_club.models import BooksRead
from chores.models import EarnedWage

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    stats = UserStats.objects.filter(user=user).first()
    books = BooksRead.objects.filter(user=user)
    earnings = EarnedWage.objects.filter(user=user).first()
    xp_settings = XPSettings.objects.first()
    xp_logs = XPLog.objects.filter(user=user).order_by('-date_awarded')

    # === Calculate next level XP and XP needed ===
    if stats and xp_settings:
        next_level_xp = ( (stats.level + 1) ** (1 / xp_settings.exponent) ) * xp_settings.base
        xp_to_next = next_level_xp - stats.xp
        progress_percent = (stats.xp / next_level_xp) * 100
    else:
        next_level_xp = 0
        xp_to_next = 0
        progress_percent = 0

    context = {
        'profile_user': user,
        'stats': stats,
        'books': books,
        'earnings': earnings,
        'xp_settings': xp_settings,
        'next_level_xp': int(next_level_xp),
        'xp_to_next': int(xp_to_next),
        'progress_percent': int(progress_percent),
        'xp_logs': xp_logs,
    }
    return render(request, 'accounts/user_profile.html', context)

def register(request):
    """Register a new user."""
    if request.method != 'POST':
        # Display blank registration form.
        form = UserCreationForm()
    else:
        # Process completed form.
        form = UserCreationForm(data=request.POST)

        if form.is_valid():
            new_user = form.save()
            # Log the user in and then redirect to home page.
            login(request, new_user)
            return redirect('household_main:index')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'registration/register.html', context)