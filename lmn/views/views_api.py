import requests
from ..models import Artist, Venue, Show
from django.http import HttpResponse, HttpResponseServerError
import os
import logging
from urllib import parse
from django.core.exceptions import ObjectDoesNotExist
from dotenv import load_dotenv


# Load the environment variables from .env file
load_dotenv()

# Get the API keys from the environment variables
key = os.getenv('TICKETMASTER_KEY')
baseUrl = 'https://app.ticketmaster.com/discovery/v2/'
unavailable_message = 'There was a problem, try again later. Error: '


def get_artist(request):
    """
    Retrieves music artists from the Ticketmaster API and saves them to the database.

    Returns:
        HttpResponse: A response indicating whether the artists have been populated successfully or not.
    """
    
    artist_list = []

    try:

        if not key:
            raise ValueError('TICKETMASTER_KEY not found in environment variables')

        # Set the query parameters to retrieve music events in Minneapolis.
        query = {'classificationName': 'music', 'dmaId': '336'}
        # Construct the API URL using the base URL, query parameters, and API key.
        url = '{}events.json?{}&apikey={}'.format(baseUrl, parse.urlencode(query), key)
        response = requests.get(url.strip())
        # Raise an exception if the response status code is not 200 OK.
        response.raise_for_status()
        data = response.json()
        # Get the list of events from the response object.
        results = data['_embedded']['events']

        # Loop through each event to get the artist name and add it to the artist list.
        for result in results:
            artist_name = result['_embedded']['attractions'][0]['name']

            if artist_name not in artist_list:
                artist_list.append(artist_name)
                Artist(name=artist_name).save()

        return HttpResponse('Artists have been populated correctly.', status=200)

    except Exception as e:
        logging.error(f'Error: {e}')
        return HttpResponseServerError (unavailable_message + str(e), status=500)


def get_venue(request):
    """
    Retrieves music venues from the Ticketmaster API and saves them to the database.

    Returns:
        HttpResponse: A response indicating whether the venues have been populated successfully or not.
    """

    try:

        if not key:
            raise ValueError('TICKETMASTER_KEY not found in environment variables')

        #Set the query parameters to retreive venues in Minnesota.
        query = {'classificationName': 'music', 'stateCode': 'MN'}
        # Construct the API URL using the base URL, query parameters, and API key.
        url = '{}venues.json?{}&apikey={}'.format(baseUrl, parse.urlencode(query), key)
        response = requests.get(url.strip())
        # Raise an exception if the response status code is not 200 OK.
        response.raise_for_status()
        data = response.json()
        # Get the list of venues from the parsed data.
        results = data['_embedded']['venues']
        
        # Loop through the list of venues and save each venue to the database.
        for result in results:
            venue_name = result['name']
            venue_city = result['city']['name']
            venue_state = result['state']['name']

            Venue(name=venue_name, city=venue_city, state=venue_state).save()

        return HttpResponse('Venues have been populated correctly.', status=200)

    except Exception as e:
        logging.error(f'Error: {e}')
        return HttpResponseServerError (unavailable_message + str(e), status=500)


def get_show(request):
    """
    Retrieves music shows from the Ticketmaster API and saves them to the database.

    Returns:
        HttpResponse: A response indicating whether the shows have been populated successfully or not.
    """

    try:

        if not key:
            raise ValueError('TICKETMASTER_KEY not found in environment variables')

        # Set the query parameters to retrieve music events in Minneapolis.
        query = {'classificationName': 'music', 'dmaId': '336'}
        # Construct the API URL using the base URL, query parameters, and API key.
        url = '{}events.json?{}&apikey={}'.format(baseUrl, parse.urlencode(query), key)
        response = requests.get(url.strip())
        data = response.json()
        results = data['_embedded']['events']

        # Loop through the results and extract relevant information to create Show objects in the database.
        for result in results:
            # Extract artist name, venue name, and show date time from the API response.
            artist_name = result['_embedded']['attractions'][0]['name']
            venue_name = result['_embedded']['venues'][0]['name']
            
            try:
                show_date_time = result['dates']['start']['dateTime']
            except KeyError:
                logging.warning(f"No 'dateTime' key found in the 'start' key of the 'dates' dictionary for event {result['id']}. Skipping this event.")
                continue
            except Exception as e:
                logging.error(f"Error extracting 'dateTime' from event {result['id']}: {e}")
                continue

            # Try to retrieve the artist and venue objects from the database using their names.
            # If they do not exist, log a warning and skip creating the show object.
            try:
                artist = Artist.objects.get(name=artist_name)
            except ObjectDoesNotExist:
                logging.warning(f"Artist '{artist_name}' does not exist in the database.")
                continue

            try:
                venue = Venue.objects.get(name=venue_name)
            except ObjectDoesNotExist:
                logging.warning(f"Venue '{venue_name}' does not exist in the database.")
                continue

            # Create a Show object in the database using the extracted information.
            Show(show_date=show_date_time, artist=artist, venue=venue).save()

        return HttpResponse('Shows have been populated correctly.', status=200)

    except Exception as e:
        logging.error(f'Error: {e}')
        return HttpResponseServerError (unavailable_message + str(e), status=500)
