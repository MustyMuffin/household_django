import time
from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User
from django.db import models
from django.http import Http404,JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from accounts.badge_helpers import check_and_award_badges, BadgeProgressProvider
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from chores.utils import process_chore_completion
from chores.forms import ChoreEntryForm, PartialPayoutForm
from chores.models import Chore, EarnedWage, ChoreEntry, PayoutLog


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
        chore = Chore.objects.get(text=milestone)
        # print(f"✅ Matched chore by text: {chore.text}")
        return ChoreEntry.objects.filter(user=user, chore=chore).count()
    except Chore.DoesNotExist:
        # print(f"❌ Chore not found for text: {milestone}")
        return 0

def chores_by_category(request):
    # Group chores by their category
    chores_by_category = defaultdict(list)

    all_chores = Chore.objects.all()

    for item in all_chores:
        category_name = item.chore_category.name if item.chore_category else "Uncategorized"
        chores_by_category[category_name].append(item)

    context = {'chores_by_category': dict(chores_by_category)}
    return render(request, 'chores/chores_by_category.html', context)

def chores(request):
    """Show all Chores."""
    chore_names = Chore.objects.order_by('text')
    context = {'chores': chore_names}
    return render(request, 'chores/chores.html', context)

def chore(request, chore_id):
    """Show a single chore and all its entries."""
    chore_name = Chore.objects.get(id=chore_id)
    chore_entries = chore_name.choreentry_set.order_by('-date_added')
    context = {'chore': chore_name, 'chore_entries': chore_entries}
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

def is_privileged(user):
    return user.groups.filter(name='Privileged').exists()

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
        'can_payout': is_privileged(request.user),
    }
    return render(request, 'chores/payout.html', context)

@login_required
def reset_earned_wage(request, user_id):
    earned = get_object_or_404(EarnedWage, user_id=user_id)
    earned.earnedSincePayout = 0
    earned.save()
    return redirect('chores:payout')
