from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import TemplateView
from accounts.models import UserStats, XPSettings, XPLog, Badge, UserBadge
from book_club.models import BooksRead, BookEntry, Book, WordsRead
from chores.models import EarnedWage, ChoreEntry, Chore
from itertools import chain
from operator import itemgetter
from accounts.xp_utils import XPManager
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from chores.models import ChoreEntry
from book_club.models import BooksRead
from django.db.models import Count
from accounts.badge_helpers import BadgeProgressProvider


class AllBadges(LoginRequiredMixin, View):
    def get(self, request):
        app_label_filter = request.GET.get('app_label')
        milestone_filter = request.GET.get('milestone_type')
        sort_mode = request.GET.get('sort', 'default')

        all_badges = Badge.objects.all()

        if app_label_filter:
            all_badges = all_badges.filter(app_label=app_label_filter)

        if milestone_filter:
            all_badges = all_badges.filter(milestone_type=milestone_filter)

        awarded_badges = UserBadge.objects.filter(user=request.user)
        awarded_ids = set(awarded_badges.values_list('badge_id', flat=True))

        badge_data = []
        for badge in all_badges:
            is_unlocked = badge.id in awarded_ids
            awarded_at = awarded_badges.get(badge_id=badge.id).awarded_at if is_unlocked else None
            raw_progress = badge.get_progress_for_user(request.user, return_raw=True)
            progress_percent = None if is_unlocked else badge.get_progress_for_user(request.user)

            badge_data.append({
                'badge': badge,
                'is_unlocked': is_unlocked,
                'awarded_at': awarded_at,
                'progress_percent': progress_percent,
                'current_value': raw_progress
            })

        milestone_types = (
            Badge.objects
            .filter(app_label=app_label_filter)
            .values_list('milestone_type', flat=True)
            .distinct()
            if app_label_filter else
            Badge.objects.values_list('milestone_type', flat=True).distinct()
        )

        sort_mode = request.GET.get('sort', 'default')

        badge_data.sort(
            key=lambda b: (
                not b['is_unlocked'],
                -(b['progress_percent'] or 0) if b['progress_percent'] is not None else 0
            )
        )

        context = {
            'badges': badge_data,
            'milestone_types': milestone_types,
            'app_labels': Badge.objects.values_list('app_label', flat=True).distinct(),
            'active_app_label': app_label_filter,
            'active_filter': milestone_filter,
            'sort_mode': sort_mode
        }
        return render(request, 'accounts/all_badges.html', context)


@BadgeProgressProvider.register("book_club")
def book_club_progress(badge, user):
    milestone_type = badge.milestone_type

    if milestone_type == "books_read":
        return BooksRead.objects.filter(user=user).count()

    elif milestone_type == "words_read":
        words = WordsRead.objects.filter(user=user).first()
        return words.wordsLifetime if words else 0

    # elif milestone_type == "specific_book":
    #     # For now, return 1 if they've read it, or 0
    #     return 1 if BooksRead.objects.filter(user=user, book_name=badge.name).exists() else 0

    return 0

class MilestoneTypeOptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        app_label = request.GET.get("app_label")

        if not app_label:
            return JsonResponse({'options': []})

        milestone_types = (
            Badge.objects.filter(app_label=app_label)
            .values_list('milestone_type', flat=True)
            .distinct()
        )
        return JsonResponse({'options': list(milestone_types)})

def get_milestone_options(request):
    app = request.GET.get("app")
    initial = request.GET.get("initial")
    print(f"[DEBUG] app={app}, initial={initial}")

    if app == "chores":
        chores = Chore.objects.all()
        options = [{"id": "earned_wage", "name": "Total Wage Earned"}] + [
            {"id": str(chore.id), "name": chore.text} for chore in chores
        ]
        return JsonResponse({"options": options, "initial": initial})

    elif app == "book_club":
        data = {
            "options": [
                {"id": "books_read", "name": "Books Read"},
                {"id": "words_read", "name": "Words Read"},
                # {"id": "specific_book", "name": "Specific Book"},
            ],
            "initial": initial
        }
        return JsonResponse(data)

    return JsonResponse({"options": []})


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

            WordsRead.objects.get_or_create(user=new_user, wordsLifetime=0)

            login(request, new_user)
            return redirect('household_main:index')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'registration/register.html', context)