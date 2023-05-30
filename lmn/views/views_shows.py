from django.shortcuts import render
from django.db.models import Count

from ..models import Show


def shows_with_most_notes(request):
    """ Get the the most recent Shows with the top 5 count of notes.
    Also, get all of the notes associated with each Show. """

    # Get the top 5 shows with the most notes by getting the count and ordering first by most recent show date, then number of notes. 
    # Exclude shows with 0 notes.
    top_5_shows = Show.objects.annotate(num_notes=Count('note')).exclude(num_notes=0).order_by('-show_date', '-num_notes')[:5]  # Adapted from Django docs https://docs.djangoproject.com/en/4.2/topics/db/aggregation/
    
    for show in top_5_shows:
        show.notes = show.note_set.all() # Get data on the Note objects associated with each Show

    return render(request, 'lmn/shows/shows_with_most_notes.html', {'top_5_shows': top_5_shows})