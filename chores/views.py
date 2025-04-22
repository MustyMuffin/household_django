from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from collections import defaultdict
from decimal import Decimal

from accounts.models import XPLog
# from django.http import Http404

from .models import Chore, EarnedWage, ChoreEntry, ChoreCategory
from .forms import ChoreEntryForm

def chores_by_category(request):
    # Group chores by their category
    chores_by_category = defaultdict(list)

    all_chores = Chore.objects.all()

    for item in all_chores:
        category_name = item.chore_category.name if item.chore_category else "Uncategorized"
        chores_by_category[category_name].append(item)

    print("Categories in view context:", chores_by_category.keys())

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
    chore = Chore.objects.get(id=chore_id)
    # payment = chore.wage
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = ChoreEntryForm(data=request.POST)
    else:
        # POST data submitted; process data.
        form = ChoreEntryForm(data=request.POST)
        if form.is_valid():
            new_chore_entry = form.save(commit=False)
            new_chore_entry.chore = chore
            new_chore_entry.user = request.user
            new_chore_entry.save()

            earned_wage, created = EarnedWage.objects.get_or_create(user=request.user)
            earned_wage.earnedLifetime += Decimal(chore.wage)
            earned_wage.earnedSincePayout += Decimal(chore.wage)
            earned_wage.save()

            xp_awarded = XPLog.objects.filter(user=request.user).order_by('-date_awarded').first()

            if xp_awarded:
                messages.success(request, f"You earned {xp_awarded.amount} XP for completing a chore!")

            return redirect('chores:chores_by_category')

            return redirect('chores:chore', chore_id=chore_id)

    # Display a blank or invalid form.
    context = {'chore': chore, 'form': form}
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

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def edit_chore_entry(request, chore_entry_id):
#     """Edit an existing entry."""
#     chore_entry = ChoreEntry.objects.get(id=chore_entry_id)
#
#     if request.method != 'POST':
#         # Initial request; pre-fill form with the current entry.
#         form = ChoreEntryForm(instance=chore_entry)
#     else:
#         # POST data submitted; process data.
#         form = ChoreEntryForm(instance=chore_entry, data=request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('chores:chore', chore_id=chore.id)
#
#     context = {'chore_entry': chore_entry, 'chore': chore, 'form': form}
#     return render(request, '/chores/edit_chore_entry/<int:chore_entry_id>.html', context)