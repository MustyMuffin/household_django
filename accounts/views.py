from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import UserStats, XPSettings, XPLog, Badge, UserBadge
from book_club.models import BooksRead, BookEntry
from chores.models import EarnedWage, ChoreEntry, Chore
from itertools import chain
from operator import itemgetter
from accounts.xp_utils import XPManager
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template.loader import render_to_string

from accounts.badge_helpers import check_and_award_badges

@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    stats = UserStats.objects.filter(user=user).first()
    books = BooksRead.objects.filter(user=user)
    earnings = EarnedWage.objects.filter(user=user).first()
    xp_logs = XPLog.objects.filter(user=user).order_by('-date_awarded')
    date_awarded = UserBadge.objects.filter(user=user).order_by('-awarded_at')

    # Default values
    xp = 0
    level = 1
    next_level_xp = 100
    xp_to_next = 100
    progress_percent = 0

    if stats:
        xp = stats.xp
        level = stats.level
        next_level_xp = XPManager.next_level_xp(level)
        xp_to_next_level = XPManager.xp_to_next_level(xp, level)
        progress_percent = XPManager.progress_percent(xp, level)
        user_badge = UserBadge.objects.filter(user=user).select_related('badge')
        # badge_progress = check_and_award_badges.get_user_progress(user)

    context = {
        'profile_user': user,
        'stats': stats,
        'books': books,
        'earnings': earnings,
        'xp_logs': xp_logs,
        'xp': xp,
        'level': level,
        'next_level_xp': next_level_xp,
        'xp_to_next_level': xp_to_next_level,
        'progress_percent': progress_percent,
        'user_badge': user_badge,
        'date_awarded': date_awarded,
        # 'badge_progress': badge_progress,
    }

    return render(request, 'accounts/user_profile.html', context)


@login_required
def all_badges(request):
    badges = Badge.objects.all().order_by('module')
    context = {
        'badges': badges
    }
    return render(request, 'accounts/all_badges.html', context)

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

    grouped_activity = []
    last_group_time = None
    current_group = []

    for entry in combined:
        if not last_group_time or abs((entry['timestamp'] - last_group_time)) > timedelta(seconds=1):
            if current_group:
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


@staff_member_required
def get_milestone_options(request):
    app = request.GET.get("app")
    # print(f"[DEBUG] get_milestone_options called for app: {app}")

    if app == 'chores':
        chores = Chore.objects.all()
        html = render_to_string("admin/accounts/badge/milestone_field_chores.html", {"chores": chores})
        return HttpResponse(html)

    return HttpResponse(render_to_string("admin/accounts/badge/milestone_field_charfield.html"))

# def user_badges_view(request):
#     filter_option = request.GET.get('filter', 'all')
#     sort_option = request.GET.get('sort', 'default')
#
#     badges = Badge.objects.all()
#     user_badges = UserBadge.objects.filter(user=request.user)
#     user_badge_map = {ub.badge_id: ub for ub in user_badges}
#
#     badge_list = []
#
#     for badge in badges:
#         user_badge = user_badge_map.get(badge.id)
#         if user_badge:
#             badge.progress = user_badge.progress
#             badge.progress_percent = min(int((user_badge.progress / badge.requirement) * 100), 100)
#             badge.earned = user_badge.earned
#         else:
#             badge.progress = 0
#             badge.progress_percent = 0
#             badge.earned = False
#
#         # Apply filter
#         if filter_option == 'earned' and not badge.earned:
#             continue
#         if filter_option == 'locked' and badge.earned:
#             continue
#
#         badge_list.append(badge)
#
#     # Apply sorting
#     if sort_option == 'progress':
#         badge_list.sort(key=lambda b: b.progress_percent, reverse=True)
#
#     context = {
#         'badges': badge_list,
#         'current_filter': filter_option,
#         'current_sort': sort_option,
#     }
#     return render(request, 'accounts/all_badges.html', context)

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