from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404

from .models import Note, Entry
from .forms import NoteForm, EntryForm


def index(request):
    """The home page for Household."""
    return render(request, 'household_main/index.html')

@login_required
def notes(request):
    """Show all Notes."""
    notes = Note.objects.filter(owner=request.user).order_by('date_added')
    context = {'notes': notes}
    return render(request, 'household_main/notes.html', context)

@login_required
def note(request, note_id):
    """Show a single note and all its entries."""
    note = Note.objects.get(id=note_id)
    # Make sure the note belongs to the current user.
    if note.owner != request.user:
        raise Http404

    entries = note.entry_set.order_by('-date_added')
    context = {'note': note, 'entries': entries}
    return render(request, 'household_main/note.html', context)

@login_required
def new_note(request):
    """Add a new note."""
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = NoteForm()
    else:
        # POST data submitted; process data.
        form = NoteForm(data=request.POST)
        if form.is_valid():
            new_note = form.save(commit=False)
            new_note.owner = request.user
            new_note.save()
            return redirect('household_main:notes')
 
    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'household_main/new_note.html', context)

@login_required
def new_entry(request, note_id):
    """Add a new entry for a particular note."""
    note = Note.objects.get(id=note_id)

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = EntryForm()
    else:
        # POST data submitted; process data.
        form = EntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.note = note
            new_entry.save()
            return redirect('household_main:note', note_id=note_id)

    # Display a blank or invalid form
    context = {'note': note, 'form': form}
    return render(request, 'household_main/new_entry.html', context)

@login_required
def edit_entry(request, entry_id):
    """Edit an existing entry."""
    entry = Entry.objects.get(id=entry_id)
    note = entry.note

    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.
        form = EntryForm(instance=entry)
    else:
        # POST data submitted; process data.
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('household_main:note', note_id=note.id)

    context = {'entry': entry, 'note': note, 'form': form}
    return render(request, 'household_main/edit_entry.html', context)