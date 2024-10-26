from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# from django.http import Http404

from .models import Chores, ChoreEntry
from .forms import ChoreEntryForm

def chores(request):
    """Show all Chores."""
    chores = Chores.objects.order_by('text')
    context = {'chores': chores}
    return render(request, 'chores/chores.html', context)

def chore(request, chore_id):
    """Show a single chore and all its entries."""
    chore = Chores.objects.get(id=chore_id)
    chore_entries = ChoreEntry.objects.order_by('-date_added')
    context = {'chore': chore, 'chore_entries': chore_entries}
    return render(request, 'chores/chore.html', context)

@login_required    
def new_chore_entry(request, chore_id):
    """Add a new entry for a chore."""
    chore = Chores.objects.get(id=chore_id)
    
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = ChoreEntryForm(username=request.user, data=request.POST)
    else:
        # POST data submitted; process data.
        form = ChoreEntryForm(username=request.user, data=request.POST)
        if form.is_valid():
            new_chore_entry = form.save(commit=False)
            new_chore_entry.chore = chore
            new_chore_entry.save()
            return redirect('chores:chore', chore_id=chore_id)

    # Display a blank or invalid form.
    context = {'chore': chore, 'form': form}
    return render(request, 'chores/new_chore_entry.html', context)

@login_required
def edit_chore_entry(request, chore_entry_id):
    """Edit an existing entry."""
    chore_entry = ChoreEntry.objects.get(id=chore_entry_id)
    chore = chore_entry.chore
    # if chore.owner != request.user:
    #     raise Http404

    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.
        form = ChoreEntryForm(instance=chore_entry)
    else:
        # POST data submitted; process data.
        form = ChoreEntryForm(instance=chore_entry, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('chores:chore', chore_id=chore.id)

#     context = {'chore_entry': chore_entry, 'chore': chore, 'form': form}
#     return render(request, 'chores/edit_chore_entry.html', context)