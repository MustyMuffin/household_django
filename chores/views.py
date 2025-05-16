from collections import defaultdict
import time
from django.urls import reverse
from decimal import Decimal
from accounts.badge_helpers import check_and_award_badges
from accounts.badge_helpers import check_and_award_badges, BadgeProgressProvider
from accounts.models import UserStats
from accounts.xp_helpers import award_xp
from django.http import Http404
from accounts.xp_helpers import award_xp
from chores.models import Chore, ChoreEntry
from django.contrib import messages
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ChoreEntryForm
from .models import Chore, EarnedWage, ChoreEntry


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
        if form.is_valid():
            new_chore_entry = form.save(commit=False)
            new_chore_entry.chore = chore
            new_chore_entry.user = request.user
            new_chore_entry.wage = chore.wage
            new_chore_entry.save()

            # Update Earnings
            earned_wage, _ = EarnedWage.objects.get_or_create(user=request.user)
            earned_wage.earnedLifetime += Decimal(chore.wage)
            earned_wage.earnedSincePayout += Decimal(chore.wage)
            earned_wage.save()

            # Check and award badges
            current_count = ChoreEntry.objects.filter(user=request.user, chore=chore).count()
            check_and_award_badges(
                user=request.user,
                app_label="chores",
                milestone_type=chore.text,
                current_value=current_count,
                request=request
            )
            check_and_award_badges(
                user=request.user,
                app_label="chores",
                milestone_type="earned_wage",
                current_value=chore.wage,
                request=request
            )

            # Award XP
            result = award_xp(
                user=request.user,
                source_object=chore,
                reason=f"Completed chore: {chore.text}",
                source_type="chore",
                request=request
            )

            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                print("DEBUG: requests.headers returned success")
                return JsonResponse({
                    "success": True,
                    "xp_awarded": str(result["xp_awarded"]),
                    "message": f"You earned {result['xp_awarded']} XP for completing a chore!",
                    "redirect_url": reverse("chores:chores_by_category")
                })

            messages.success(request, f"✅ You earned {result['xp_awarded']} XP for completing a chore!")
            return redirect('chores:chores_by_category')

        else:
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                print("DEBUG: requests.headers returned FAIL")
                return JsonResponse({
                    "success": False,
                    "error": "Form validation failed. Please check your input."
                }, status=400)

    context = {
        'chore': chore,
        'form': form,
    }
    return render(request, 'chores/new_chore_entry.html', context)



def payout(request):
    # Current user info
    earner = EarnedWage.objects.get(user=request.user)
    wage_earned = earner.earnedSincePayout

    # All users' earnings
    all_earners = EarnedWage.objects.select_related('user').all()

    context = {
        'wage_earned': wage_earned,
        'earner': earner,
        'all_earners': all_earners,
    }
    return render(request, 'chores/payout.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reset_earned_wage(request, user_id):
    earned = get_object_or_404(EarnedWage, user_id=user_id)
    earned.earnedSincePayout = 0
    earned.save()
    return redirect('chores:payout')