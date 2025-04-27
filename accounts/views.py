from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import UserStats, XPSettings, XPLog
from book_club.models import BooksRead, BookEntry
from chores.models import EarnedWage, ChoreEntry

from itertools import chain
from operator import itemgetter

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    stats = UserStats.objects.filter(user=user).first()
    books = BooksRead.objects.filter(user=user)
    earnings = EarnedWage.objects.filter(user=user).first()
    xp_settings = XPSettings.objects.first()
    xp_logs = XPLog.objects.filter(user=user).order_by('-date_awarded')

    # === Calculate next level XP and XP needed ===
    # if stats and xp_settings:
    #     next_level_xp = ( (stats.level + 1) ** (1 / xp_settings.exponent) ) * xp_settings.base
    #     xp_to_next = next_level_xp - stats.xp
    #     progress_percent = (stats.xp / next_level_xp) * 100
    # else:
    #     next_level_xp = 0
    #     xp_to_next = 0
    #     progress_percent = 0

    if stats and xp_settings:
        print("DEBUG: stats.level =", stats.level)
        print("DEBUG: xp_settings.exponent =", xp_settings.exponent)
        print("DEBUG: xp_settings.base =", xp_settings.base)

        next_level_xp = ((stats.level + 1) ** (1 / xp_settings.exponent)) * xp_settings.base
        print("DEBUG: next_level_xp =", next_level_xp)

        xp_to_next = next_level_xp - stats.xp
        print("DEBUG: stats.xp =", stats.xp)
        print("DEBUG: xp_to_next =", xp_to_next)

        progress_percent = (stats.xp / next_level_xp) * 100
        print("DEBUG: progress_percent =", progress_percent)

    else:
        print("DEBUG: stats or xp_settings missing, setting defaults to 0")

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

def activity_feed(request):
    show_all_users = True

    if show_all_users:
        book_entries = BookEntry.objects.select_related('user').all()
        chore_entries = ChoreEntry.objects.select_related('user').all()
        xp_logs = XPLog.objects.select_related('user').all()
    else:
        book_entries = BookEntry.objects.filter(user=request.user)
        chore_entries = ChoreEntry.objects.filter(user=request.user)
        xp_logs = XPLog.objects.filter(user=request.user)

    book_entries = [
        {'type': 'book', 'user': entry.user, 'timestamp': entry.date_added, 'info': f"Read book: {entry.book.text}", 'xp': 0}
        for entry in book_entries
    ]

    chore_entries = [
        {'type': 'chore', 'user': entry.user, 'timestamp': entry.date_added, 'info': f"Completed chore: {entry.chore.text}", 'xp': 0}
        for entry in chore_entries
    ]

    xp_logs = [
        {'type': 'xp', 'user': log.user, 'timestamp': log.date_awarded, 'info': f"Gained XP: {log.reason}", 'xp': log.amount}
        for log in xp_logs
    ]

    combined = sorted(
        chain(book_entries, chore_entries, xp_logs),
        key=itemgetter('timestamp'),
        reverse=True
    )

    # Group by timestamp within a small time window
    grouped_activity = []
    last_group_time = None
    current_group = []

    for entry in combined:
        if not last_group_time or abs((entry['timestamp'] - last_group_time)) > timedelta(seconds=1):
            if current_group:
                # Compute XP sum for the previous group
                total_xp = sum(item['xp'] for item in current_group)
                grouped_activity.append({'items': current_group, 'total_xp': total_xp})
            current_group = [entry]
            last_group_time = entry['timestamp']
        else:
            current_group.append(entry)

    if current_group:
        total_xp = sum(item['xp'] for item in current_group)
        grouped_activity.append({'items': current_group, 'total_xp': total_xp})

    context = {'grouped_activity': grouped_activity}
    return render(request, 'accounts/activity_feed.html', context)

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