import time
from collections import defaultdict
from django.core.paginator import Paginator
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import Http404,JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from accounts.badge_helpers import check_and_award_badges, BadgeProgressProvider
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from chores.utils import process_chore_completion, get_chore_stats_days
from chores.forms import ChoreEntryForm, PartialPayoutForm, ChoreForm, ChoreEntryEditForm
from chores.models import Chore, EarnedWage, ChoreEntry, PayoutLog, ChoreCategory
from datetime import timedelta
from functools import wraps

def is_privileged(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not user.groups.filter(name='Privileged').exists():
            return redirect('not_authorized')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_is_privileged(user):
    """
    Simple function to check if a user has privilege.
    """
    return user.is_authenticated and user.groups.filter(name='Privileged').exists()

@is_privileged
@login_required
def add_new_chore(request):
    if request.method == "POST":
        form = ChoreForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            wage = form.cleaned_data.get("wage")

            selected_cat_id = request.POST.get("selected_cat_id")
            new_category_name = request.POST.get("new_category_name", "").strip()
            category = None

            if selected_cat_id == "new" and new_category_name:
                category, _ = ChoreCategory.objects.get_or_create(name=new_category_name)
            elif selected_cat_id:
                category = ChoreCategory.objects.filter(id=selected_cat_id).first()

            if not category:
                messages.error(request, "Please select or create a valid category.")
                return render(request, "chores/add_new_chore.html", {"form": form})

            Chore.objects.create(
                name=name,
                wage=wage or Decimal("0.00"),
                category=category
            )

            messages.success(request, "✅ New chore added successfully.")
            return redirect("chores:chores_by_category")

    else:
        form = ChoreForm()

    return render(request, "chores/add_new_chore.html", {"form": form})

@BadgeProgressProvider.register("chores")
def chore_progress(badge, user):
    milestone = badge.milestone_type
    # print(f"DEBUG milestone: {milestone} ({type(milestone)})")

    if milestone == "earned_wage":
        # print("✅ Chore badge with earned_wage milestone matched")
        return ChoreEntry.objects.filter(user=user).aggregate(
            total=models.Sum("wage")
        )["total"] or 0

    try:
        chore = Chore.objects.get(name=milestone)
        # print(f"✅ Matched chore by name: {chore.name}")
        return ChoreEntry.objects.filter(user=user, chore=chore).count()
    except Chore.DoesNotExist:
        # print(f"❌ Chore not found for name: {milestone}")
        return 0

def chores_by_category(request):
    # Group chores by their category
    chores_by_category = defaultdict(list)

    all_chores = Chore.objects.all()

    for item in all_chores:
        category_name = item.category.name if item.category else "Uncategorized"
        chores_by_category[category_name].append(item)

    context = {'chores_by_category': dict(chores_by_category)}
    return render(request, 'chores/chores_by_category.html', context)

def chores(request):
    """Show all Chores."""
    chore_names = Chore.objects.order_by('name')
    context = {'chores': chore_names}
    return render(request, 'chores/chores.html', context)

@login_required
def chore(request, chore_id):
    """Show a single chore and all its entries."""
    chore_name = Chore.objects.get(id=chore_id)
    chore_entries = chore_name.choreentry_set.order_by('-date_added')
    chore_description = chore_name.description

    context = {
        'chore': chore_name,
        'chore_entries': chore_entries,
        'chore_description': chore_description,
    }

    return render(request, 'chores/chore.html', context)

@login_required
def new_chore_entry(request, chore_id):
    """Add a new entry for a chore."""
    chore = get_object_or_404(Chore, id=chore_id)

    if request.method != 'POST':
        form = ChoreEntryForm()
    else:
        form = ChoreEntryForm(data=request.POST)
        entry, result, redirect_url, success = process_chore_completion(
            user=request.user, chore=chore, request=request, form=form
        )

        if success:
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JsonResponse({
                    "success": True,
                    "xp_awarded": str(result["xp_awarded"]),
                    "message": f"You earned {result['xp_awarded']} XP for completing a chore!",
                    "redirect_url": redirect_url
                })

            messages.success(request, f"✅ You earned {result['xp_awarded']} XP for completing a chore!")
            return redirect(redirect_url)

        else:
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JsonResponse({
                    "success": False,
                    "error": "Form validation failed. Please check your input."
                }, status=400)

    context = {
        'chore': chore,
        'form': form,
    }
    return render(request, 'chores/new_chore_entry.html', context)

@is_privileged
@login_required
def edit_chore_entry(request, chore_id, entry_id=None):
    """
    View to edit a chore entry's timestamp and other details.
    Only accessible to privileged users.
    """
    # Get the chore
    chore = get_object_or_404(Chore, id=chore_id)

    # Check if user is privileged
    if not is_privileged(request.user):
        raise PermissionDenied("You don't have permission to edit chore entries.")

    # Get the entry to edit
    if entry_id:
        entry = get_object_or_404(ChoreEntry, id=entry_id, chore=chore)
    else:
        # If no entry_id provided, get the most recent entry
        entry = chore.choreentry_set.order_by('-date_added').first()
        if not entry:
            messages.error(request, "No chore entries found to edit.")
            return redirect('chores:chore', chore_id=chore.id)

    if request.method == 'POST':
        form = ChoreEntryEditForm(request.POST, instance=entry)

        if form.is_valid():
            # Save the form
            updated_entry = form.save(commit=False)

            # Ensure the datetime is timezone-aware
            if updated_entry.date_added:
                # If the datetime from the form is naive, make it timezone-aware
                if timezone.is_naive(updated_entry.date_added):
                    updated_entry.date_added = timezone.make_aware(updated_entry.date_added)

            # Set who made the edit (optional - add an edited_by field to track this)
            # updated_entry.edited_by = request.user
            # updated_entry.edited_at = timezone.now()

            updated_entry.save()

            messages.success(
                request,
                f"Successfully updated chore entry for '{chore.name}'. "
                f"New completion time: {timezone.localtime(updated_entry.date_added).strftime('%Y-%m-%d %I:%M %p')}"
            )

            return redirect('chores:chore', chore_id=chore.id)
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ChoreEntryEditForm(instance=entry)

    context = {
        'chore': chore,
        'entry': entry,
        'form': form,
        'is_privileged': True,  # Since we already checked permission
    }

    return render(request, 'chores/edit_chore_entry.html', context)


@login_required
def select_chore_entry_to_edit(request, chore_id):
    """
    View to show all entries for a chore and let privileged users select which to edit.
    """
    if not is_privileged(request.user):
        raise PermissionDenied("You don't have permission to edit chore entries.")

    chore = get_object_or_404(Chore, id=chore_id)

    # Get date filtering parameter
    days_filter = request.GET.get('days', '30')  # Default to 30 days
    try:
        days = int(days_filter)
        if days <= 0:
            days = 30
    except (ValueError, TypeError):
        days = 30

    # Filter entries by date range
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = chore.choreentry_set.filter(date_added__gte=cutoff_date).order_by('-date_added')

    # Set up pagination
    paginator = Paginator(queryset, 10)  # Show 10 entries per page
    page_number = request.GET.get('page', 1)
    entries = paginator.get_page(page_number)

    # Get total counts
    total_entries_all_time = chore.choreentry_set.count()
    total_entries_filtered = queryset.count()

    # Get the most recent entry overall for "last completed" stat
    latest_entry = chore.choreentry_set.order_by('-date_added').first()

    # Available filter options
    filter_options = [
        {'value': '7', 'label': 'Past 7 days'},
        {'value': '30', 'label': 'Past 30 days'},
        {'value': '90', 'label': 'Past 3 months'},
        {'value': '365', 'label': 'Past year'},
        {'value': '999999', 'label': 'All time'},  # Large number for "all time"
    ]

    context = {
        'chore': chore,
        'entries': entries,
        'total_entries_all_time': total_entries_all_time,
        'total_entries_filtered': total_entries_filtered,
        'latest_entry': latest_entry,
        'current_days_filter': days,
        'filter_options': filter_options,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
    }

    return render(request, 'chores/select_entry_to_edit.html', context)

@require_POST
def payout_partial(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    earned_wage = get_object_or_404(EarnedWage, user=user)

    try:
        payout_amount = Decimal(request.POST.get('payout_amount', '0'))
    except Exception:
        messages.error(request, "Invalid payout amount.")
        return redirect('chores:payout_summary')

    if 0 < payout_amount <= earned_wage.earnedSincePayout:
        earned_wage.earnedSincePayout -= payout_amount
        earned_wage.save()

        PayoutLog.objects.create(
            user=user,
            amount=payout_amount,
            performed_by=request.user
        )

        messages.success(request, f"💸 Paid out ${payout_amount:.2f} to {user.username}.")
    else:
        messages.error(request, "Invalid payout amount.")

    return redirect('chores:payout_summary')

@login_required
def payout_summary(request):
    all_earners = EarnedWage.objects.select_related('user').all()
    wage_earned = 0
    if hasattr(request.user, 'earnedwage'):
        wage_earned = request.user.earnedwage.earnedSinceLastPayout

    logs = PayoutLog.objects.select_related('user', 'performed_by').order_by('-created_at')[:25]  # last 25 logs

    context = {
        'all_earners': all_earners,
        'wage_earned': wage_earned,
        'logs': logs,
    }
    return render(request, 'chores/payout_summary.html', context)


@login_required
def payout(request):
    # Current user info


    earner = EarnedWage.objects.get(user=request.user)
    wage_earned = earner.earnedSincePayout

    # All users' earnings
    all_earners = EarnedWage.objects.select_related('user').all()

    logs = PayoutLog.objects.select_related('user', 'performed_by').order_by('-created_at')[:25]

    context = {
        'wage_earned': wage_earned,
        'all_earners': all_earners,
        'logs': logs,
        'can_payout': user_is_privileged(request.user),
    }
    return render(request, 'chores/payout.html', context)

@login_required
def reset_earned_wage(request, user_id):
    earned = get_object_or_404(EarnedWage, user_id=user_id)
    earned.earnedSincePayout = 0
    earned.save()
    return redirect('chores:payout')


@login_required
def chore_analytics(request):
    stats = get_chore_stats_days(7)  # default to 7-day period

    context = {
        'all_chores': Chore.objects.all(),
        # unpack stats explicitly for template readability
        'top_users': stats["top_users"],
        'top_chores': stats["top_chores"],
        'user_chore_breakdown': stats["user_chore_breakdown"],
        'per_day_breakdown': stats["per_day_breakdown"],
        'range_start': stats["range_start"],
        'range_end': stats["range_end"],
    }

    return render(request, "chores/chore_analytics.html", context)


@login_required
def chore_analytics_json(request):
    chore_id = request.GET.get("chore_id")
    try:
        days = int(request.GET.get("days", 7))
    except ValueError:
        days = 7

    try:
        chore = Chore.objects.get(id=chore_id)
    except (Chore.DoesNotExist, TypeError, ValueError):
        chore = None

    stats = get_chore_stats_days(days, chore=chore)

    html = render_to_string(
        "chores/_analytics_partial.html",
        context={
            "top_users": stats["top_users"],
            "top_chores": stats["top_chores"],
            "user_chore_breakdown": stats["user_chore_breakdown"],
            "per_day_breakdown": stats["per_day_breakdown"],
            "range_start": stats["range_start"],
            "range_end": stats["range_end"],
        },
        request=request,
    )
    return JsonResponse({"html": html})