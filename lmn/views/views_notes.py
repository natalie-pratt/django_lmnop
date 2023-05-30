""" Views related to creating and viewing Notes for shows. """

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from datetime import datetime
from django.utils import timezone

from django.core.exceptions import ValidationError

from ..models import Note, Show
from ..forms import NewNoteForm 


@login_required
def new_note(request, show_pk):
    """ Create a new note for a show. A user cannot add note for a show that has not happened yet."""
    show = get_object_or_404(Show, pk=show_pk)

    if request.method == 'POST':
        if show.in_past == False:
            return render(request, '400.html')
        else:
            form = NewNoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.user = request.user
                note.show = show
                note.save()
                return redirect('note_detail', note_pk=note.pk)
            else:
                return redirect('new_note', show_pk=show.pk)
    else:
        form = NewNoteForm()

    return render(request, 'lmn/notes/new_note.html', {'form': form, 'show': show})


@login_required
def edit_note(request, note_pk):
    """ Edit a particular note about a show. A user can only edit a note created by the user and not the note created by other users. """
    note = get_object_or_404(Note, pk=note_pk)
    form = NewNoteForm(instance=note)
    
    if request.method == 'POST':
        form = NewNoteForm(request.POST, instance=note)  # Loads the existing note data on the form
        if request.user.pk != note.user.pk:
            return render(request, '403.html')
        else:
            if form.is_valid():
                form.save()
                return redirect('note_detail', note_pk=note_pk)
            else:
                return redirect('edit_note', note_pk=note_pk)
            
    return render(request, 'lmn/notes/edit_note.html', {'form': form})
    

def latest_notes(request):
    """ Get the 20 most recent notes, ordered with most recent first. """
    notes = Note.objects.all().order_by('-posted_date')[:20]   # Slice of the 20 most recent notes
    return render(request, 'lmn/notes/note_list.html', {'notes': notes, 'title': 'Latest Notes'})


def notes_for_show(request, show_pk): 
    """ Get notes for one show, most recent first. """
    show = get_object_or_404(Show, pk=show_pk)  
    notes = Note.objects.filter(show=show_pk).order_by('-posted_date')
    return render(request, 'lmn/notes/notes_for_show.html', {'show': show, 'notes': notes})


def note_detail(request, note_pk):
    """ Display one note. """
    note = get_object_or_404(Note, pk=note_pk)
    return render(request, 'lmn/notes/note_detail.html', {'note': note})


@login_required
def delete_note(request, note_pk):
    """ Delete a particular note about a show.
    Note can only be deleted by owner of note. """
    note = get_object_or_404(Note, pk=note_pk)
    
    if request.method == 'POST':
        return redirect('delete_confirmation', note_pk=note.pk)
    else:
        return render(request, 'lmn/notes/note_detail.html', {'note': note})


def delete_confirmation(request, note_pk):
    """ Asks user for confirmation to delete note. """
    note = get_object_or_404(Note, pk=note_pk)
    
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            if request.user.pk == note.user.pk:
                note.delete()
                messages.add_message(request, messages.INFO, 'Your note has been deleted.', extra_tags='note-delete-message')  # extra_tags = CSS class
                return redirect('latest_notes')
            else:
                return render(request, '403.html')
        else:
            return redirect('note_detail', note_pk=note.pk)
    
    return render(request, 'lmn/notes/note_delete_confirmation.html', {'note' : note})
        