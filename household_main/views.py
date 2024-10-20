from django.shortcuts import render

from .models import Note

def index(request):
    """The home page for Household."""
    return render(request, 'household_main/index.html')

def notes(request):
    """Show all Notes."""
    notes = Note.objects.order_by('date_added')
    context = {'notes': notes}
    return render(request, 'household_main/notes.html', context)

def note(request, note_id):
    """Show a single note and all its entries."""
    note = Note.objects.get(id=topic_id)
    entries = note.entry_set.order_by('-date_added')
    context = {'note': note, 'entries': entries}
    return render(request, 'household_main/note.html', context)