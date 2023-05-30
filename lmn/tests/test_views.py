from django.test import TestCase, Client

from django.urls import reverse
from django.contrib import auth
from django.contrib.auth import authenticate
from django.dispatch import Signal

import re
import datetime
from datetime import timezone

from lmn.models import Note, Show
from django.contrib.auth.models import User


class TestHomePage(TestCase):

    def test_home_page_message(self):
        home_page_url = reverse('homepage')
        response = self.client.get(home_page_url)
        self.assertContains(response, 'Welcome to Live Music Notes, LMN')


class TestEmptyViews(TestCase):

    """ Main views - the ones in the navigation menu """

    def test_with_no_artists_returns_empty_list(self):
        response = self.client.get(reverse('artist_list'))
        self.assertFalse(response.context['artists'])  # An empty list is false

    def test_with_no_venues_returns_empty_list(self):
        response = self.client.get(reverse('venue_list'))
        self.assertFalse(response.context['venues'])  # An empty list is false

    def test_with_no_notes_returns_empty_list(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertFalse(response.context['notes'])  # An empty list is false

    def test_with_no_shows_returns_empty_list(self):
        response = self.client.get(reverse('shows_with_most_notes'))
        self.assertFalse(response.context['top_5_shows'])  # An empty list is false


class TestArtistViews(TestCase):

    fixtures = ['testing_artists', 'testing_venues', 'testing_shows']

    def test_all_artists_displays_all_alphabetically(self):
        response = self.client.get(reverse('artist_list'))

        # .* matches 0 or more of any character. Test to see if
        # these names are present, in the right order

        regex = '.*ACDC.*REM.*Yes.*'
        response_text = str(response.content)

        self.assertTrue(re.match(regex, response_text))
        self.assertEqual(len(response.context['artists']), 3)

    def test_artists_search_clear_link(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})

        # There is a 'clear' link on the page and, its url is the main venue page
        all_artists_url = reverse('artist_list')
        self.assertContains(response, all_artists_url)

    def test_artist_search_no_search_results(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'Queen'})
        self.assertNotContains(response, 'Yes')
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 0
        self.assertEqual(len(response.context['artists']), 0)

    def test_artist_search_partial_match_search_results(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'e'})
        # Should be two responses, Yes and REM
        self.assertContains(response, 'Yes')
        self.assertContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 2
        self.assertEqual(len(response.context['artists']), 2)

    def test_artist_search_one_search_result(self):

        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'Yes')
        self.assertContains(response, 'ACDC')
        # Check the length of artists list is 1
        self.assertEqual(len(response.context['artists']), 1)

    def test_correct_template_used_for_artists(self):
        # Show all
        response = self.client.get(reverse('artist_list'))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Search with matches
        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')
        # Search no matches
        response = self.client.get(reverse('artist_list'), {'search_name': 'Non Existant Band'})
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Artist detail
        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_detail.html')

        # Artist list for venue
        response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')

    def test_artist_detail(self):

        """ Artist 1 details displayed in correct template """
        # kwargs to fill in parts of url. Not get or post params

        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 1}))
        self.assertContains(response, 'REM')
        self.assertEqual(response.context['artist'].name, 'REM')
        self.assertEqual(response.context['artist'].pk, 1)

    def test_get_artist_that_does_not_exist_returns_404(self):
        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 10}))
        self.assertEqual(response.status_code, 404)

    def test_venues_played_at_most_recent_shows_first(self):
        # For each artist, display a list of venues they have played shows at.
        # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

        url = reverse('venues_for_artist', kwargs={'artist_pk': 1})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1, show2 = shows[0], shows[1]
        self.assertEqual(2, len(shows))

        self.assertEqual(show1.artist.name, 'REM')
        self.assertEqual(show1.venue.name, 'The Turf Club')

        # From the fixture, show 2's "show_date": "2017-02-02T19:30:00-06:00"
        expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # from the fixture, show 1's "show_date": "2017-01-02T17:30:00-00:00",
        self.assertEqual(show2.artist.name, 'REM')
        self.assertEqual(show2.venue.name, 'The Turf Club')
        expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show2.show_date, expected_date)

        # Artist 2 (ACDC) has played at venue 1 (First Ave)

        url = reverse('venues_for_artist', kwargs={'artist_pk': 2})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1 = shows[0]
        self.assertEqual(1, len(shows))

        # This show has "show_date": "2017-01-21T21:45:00-00:00",
        self.assertEqual(show1.artist.name, 'ACDC')
        self.assertEqual(show1.venue.name, 'First Avenue')
        expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # Artist 3, no shows

        url = reverse('venues_for_artist', kwargs={'artist_pk': 3})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        self.assertEqual(0, len(shows))

    def test_artist_list_displayed_on_valid_pages(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEqual(response.status_code, 200)

        artists = list(response.context['artists'])
        self.assertEqual(len(artists), 3)

        # Test first page
        response = self.client.get(reverse('artist_list') + '?page=1')
        self.assertEqual(response.status_code, 200)
        artists_on_page = list(response.context['artists'])
        self.assertEqual(len(artists_on_page), 3)
        self.assertEqual(artists_on_page[0], artists[0])
        self.assertEqual(artists_on_page[1], artists[1])
        self.assertEqual(artists_on_page[2], artists[2])

    def test_artist_list_displays_first_page_when_page_parameter_is_missing(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEqual(response.status_code, 200)
        artists_on_page = list(response.context['artists'])
        self.assertEqual(len(artists_on_page), 3)

    def test_artist_list_displays_first_page_when_page_parameter_is_zero_or_negative(self):
        response = self.client.get(reverse('artist_list') + '?page=0')
        self.assertEqual(response.status_code, 200)
        artists_on_page = list(response.context['artists'])
        self.assertEqual(len(artists_on_page), 3)

        response = self.client.get(reverse('artist_list') + '?page=-1')
        self.assertEqual(response.status_code, 200)
        artists_on_page = list(response.context['artists'])
        self.assertEqual(len(artists_on_page), 3)


class TestVenues(TestCase):

    fixtures = ['testing_venues', 'testing_artists', 'testing_shows']

    def test_with_venues_displays_all_alphabetically(self):
        response = self.client.get(reverse('venue_list'))

        # .* matches 0 or more of any character. Test to see if
        # these names are present, in the right order

        regex = '.*First Avenue.*Target Center.*The Turf Club.*'
        response_text = str(response.content)

        self.assertTrue(re.match(regex, response_text))

        self.assertEqual(len(response.context['venues']), 3)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_clear_link(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Fine Line'})

        # There is a clear link, it's url is the main venue page
        all_venues_url = reverse('venue_list')
        self.assertContains(response, all_venues_url)

    def test_venue_search_no_search_results(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Fine Line'})
        self.assertNotContains(response, 'First Avenue')
        self.assertNotContains(response, 'Turf Club')
        self.assertNotContains(response, 'Target Center')
        # Check the length of venues list is 0
        self.assertEqual(len(response.context['venues']), 0)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_partial_match_search_results(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'c'})
        # Should be two responses, Yes and REM
        self.assertNotContains(response, 'First Avenue')
        self.assertContains(response, 'Turf Club')
        self.assertContains(response, 'Target Center')
        # Check the length of venues list is 2
        self.assertEqual(len(response.context['venues']), 2)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_one_search_result(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Target'})
        self.assertNotContains(response, 'First Avenue')
        self.assertNotContains(response, 'Turf Club')
        self.assertContains(response, 'Target Center')
        # Check the length of venues list is 1
        self.assertEqual(len(response.context['venues']), 1)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_detail(self):
        # venue 1 details displayed in correct template
        # kwargs to fill in parts of url. Not get or post params
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 1}))
        self.assertContains(response, 'First Avenue')
        self.assertEqual(response.context['venue'].name, 'First Avenue')
        self.assertEqual(response.context['venue'].pk, 1)
        self.assertTemplateUsed(response, 'lmn/venues/venue_detail.html')

    def test_get_venue_that_does_not_exist_returns_404(self):
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 10}))
        self.assertEqual(response.status_code, 404)

    def test_artists_played_at_venue_most_recent_first(self):
        # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

        url = reverse('artists_at_venue', kwargs={'venue_pk': 2})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1, show2 = shows[0], shows[1]
        self.assertEqual(2, len(shows))

        self.assertEqual(show1.artist.name, 'REM')
        self.assertEqual(show1.venue.name, 'The Turf Club')

        expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        self.assertEqual(show2.artist.name, 'REM')
        self.assertEqual(show2.venue.name, 'The Turf Club')
        expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show2.show_date, expected_date)

        # Artist 2 (ACDC) has played at venue 1 (First Ave)

        url = reverse('artists_at_venue', kwargs={'venue_pk': 1})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1 = shows[0]
        self.assertEqual(1, len(shows))

        self.assertEqual(show1.artist.name, 'ACDC')
        self.assertEqual(show1.venue.name, 'First Avenue')
        expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # Venue 3 has not had any shows

        url = reverse('artists_at_venue', kwargs={'venue_pk': 3})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        self.assertEqual(0, len(shows))

    def test_correct_template_used_for_venues(self):
        # Show all
        response = self.client.get(reverse('venue_list'))
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Search with matches
        response = self.client.get(reverse('venue_list'), {'search_name': 'First'})
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Search no matches
        response = self.client.get(reverse('venue_list'), {'search_name': 'Non Existant Venue'})
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Venue detail
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/venues/venue_detail.html')

        response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')


class TestAddNoteUnauthenticatedUser(TestCase):
    # Have to add artists and venues because of foreign key constrains in show
    fixtures = ['testing_artists', 'testing_venues', 'testing_shows'] 

    def test_add_note_unauthenticated_user_redirects_to_login(self):
        response = self.client.get('/notes/add/1/', follow=True)  # Use reverse() if you can, but not required.
        # Should redirect to login; which will then redirect to the notes/add/1 page on success.
        self.assertRedirects(response, '/accounts/login/?next=/notes/add/1/')


class TestAddNotesWhenUserLoggedIn(TestCase):
    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)

    def test_save_note_for_non_existent_show_is_error(self):
        new_note_url = reverse('new_note', kwargs={'show_pk': 100})
        response = self.client.post(new_note_url)
        self.assertEqual(response.status_code, 404)

    def test_can_save_new_note_for_show_blank_data_is_error(self):
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 1})

        # No post params
        response = self.client.post(new_note_url, follow=True)
        # No note saved, should show same page
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no title
        response = self.client.post(new_note_url, {'text': 'blah blah'}, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no text
        response = self.client.post(new_note_url, {'title': 'blah blah'}, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # nothing added to database
        # 2 test notes provided in fixture, should still be 2
        self.assertEqual(Note.objects.count(), initial_note_count)   

    def test_add_note_database_updated_correctly(self):
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 1})

        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')
        self.assertEqual(new_note_query.count(), 1)

        # And one more note in DB than before
        self.assertEqual(Note.objects.count(), initial_note_count + 1)

        # Date correct?
        now = datetime.datetime.today()
        posted_date = new_note_query.first().posted_date
        self.assertEqual(now.date(), posted_date.date())  # TODO check time too

    def test_redirect_to_note_detail_after_save(self):
        new_note_url = reverse('new_note', kwargs={'show_pk': 1})
        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        new_note = Note.objects.filter(text='ok', title='blah blah').first()

        self.assertRedirects(response, reverse('note_detail', kwargs={'note_pk': new_note.pk}))


class TestUserProfile(TestCase):
    # Have to add artists and venues because of foreign key constrains in show
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    # verify correct list of reviews for a user
    def test_user_profile_show_list_of_their_notes(self):
        # get user profile for user 2. Should have 2 reviews for show 1 and 2.
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}))
        notes_expected = list(Note.objects.filter(user=2).order_by('-posted_date'))
        notes_provided = list(response.context['notes'])
        self.assertTemplateUsed('lmn/users/user_profile.html')
        self.assertEqual(notes_expected, notes_provided)

        # test notes are in date order, most recent first.
        # Note PK 3 should be first, then PK 2
        first_note = response.context['notes'][0]
        self.assertEqual(first_note.pk, 3)

        second_note = response.context['notes'][1]
        self.assertEqual(second_note.pk, 2)

    def test_user_with_no_notes(self):
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 3}))
        self.assertFalse(response.context['notes'])

    def test_username_shown_on_profile_page(self):
        # A string "username's notes" is visible
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))
        self.assertContains(response, 'alice\'s notes')

        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}))
        self.assertContains(response, 'bob\'s notes')

    def test_correct_user_name_shown_different_profiles(self):
        logged_in_user = User.objects.get(pk=2)
        self.client.force_login(logged_in_user)  # bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}))
        self.assertContains(response, 'You are logged in, <a href="/user/profile/2/">bob</a>.')

        # Same message on another user's profile. Should still see logged in message 
        # for currently logged in user, in this case, bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 3}))
        self.assertContains(response, 'You are logged in, <a href="/user/profile/2/">bob</a>.')

    def test_user_can_see_account_information(self):  # Ensure that the logged in user sees their own info on their profile
        logged_in_user = User.objects.get(pk=1)  # Alice
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))  # Alice's profile
        self.assertContains(response, 'Username: alice')
        self.assertContains(response, 'Email: a@a.com')
        self.assertContains(response, 'Full Name: alice last')

    def test_user_cannot_see_other_users_account_information(self):  # Ensure that users cannot see other users' account info
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))  # Alice's profile
        self.assertNotContains(response, 'username: alice')
        self.assertNotContains(response, 'email: a@a.com')
        self.assertNotContains(response, 'full name: alice last')

    def test_user_can_see_own_edit_button_on_profile(self):
        logged_in_user = User.objects.get(pk=3)  # cat
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 3}))  # cat's profile
        self.assertContains(response, 'Edit Account Info')  # Ensure that user's can see button including this text

    def test_user_cannot_see_edit_button_on_other_user_profile(self):
        logged_in_user = User.objects.get(pk=3)  # cat
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))  # Alice's profile
        self.assertNotContains(response, 'Edit Account Info')  # Ensure that user's cannot see button including this text

    def test_user_account_information_successfully_updated(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)
        edit_profile_url = reverse('edit_user_account_info', kwargs={'user_pk': logged_in_user.pk})
        self.client.post(
            edit_profile_url, 
            {'username': 'bobby', 'email': 'bob123@gmail.com', 'first_name': 'Bob', 'last_name': 'Browne'}, 
            follow=True
        )
        # Ensure that user's new information is the same as the post request
        updated_user = User.objects.get(pk=2)
        self.assertEqual(updated_user.username, 'bobby')
        self.assertEqual(updated_user.email, 'bob123@gmail.com')
        self.assertEqual(updated_user.first_name, 'Bob')
        self.assertEqual(updated_user.last_name, 'Browne')

    def test_user_cannot_edit_other_user_account_info(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)
        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 1})  # Alice

        response = self.client.get(edit_account_url)

        # Assert that user is redirected to the 403 template when they try to access the URL
        # of another user's account edit page
        self.assertTemplateUsed(response, '403.html')
        self.assertTemplateUsed(response, 'lmn/base.html')

    def test_request_is_made_to_own_user_account_info_not_logged_in(self):
        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 3})

        response = self.client.get(edit_account_url)  # Attempt to edit an account
        
        # Assert that the response redirects the user to the login page
        self.assertRedirects(response, '/accounts/login/?next=/user/edit_account_info/3/')

    def test_user_cannot_have_duplicate_email(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          # Alice's username
            {'username': 'bobby', 'email': 'a@a.com', 'first_name': 'Bob', 'last_name': 'Browne'}, 
            follow=True
        )    

        self.assertContains(response, 'A user with that email address already exists', status_code=200)

    def test_user_can_click_save_with_current_info_and_not_get_error(self):
        # Test that a user can go to edit account page and hit save with their own prepopulated
        # data and not get a message saying that the username or email already exists
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': 'bob','email': 'b@b.com', 'first_name': 'bob', 'last_name': 'last'},  # Bob's current information
            follow=True
        )  

        # Bob should be able to hit save with the prepopulated information without receiving these messages
        self.assertNotContains(response, 'User with this Email address already exists.', status_code=200)
        self.assertNotContains(response, 'A user with that username already exists.', status_code=200)

    def test_user_cannot_leave_username_blank(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': '','email': 'b@b.com', 'first_name': 'bob', 'last_name': 'last'},  # Bob's current information minus username
            follow=True
        )  
        
        self.assertContains(response, 'This field is required.')
        self.assertContains(response, 'Please check the data you entered')

    def test_user_cannot_leave_email_blank(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': '','email': '', 'first_name': 'bob', 'last_name': 'last'},  # Bob's current information minus email
            follow=True
        )  
        
        self.assertContains(response, 'This field is required.')
        self.assertContains(response, 'Please check the data you entered')

    def test_user_cannot_leave_first_name_blank(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': '','email': 'b@b.com', 'first_name': '', 'last_name': 'last'},  # Bob's current information minus first name
            follow=True
        )  
        
        self.assertContains(response, 'This field is required.')
        self.assertContains(response, 'Please check the data you entered')

    def test_user_cannot_leave_last_name_blank(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': '','email': 'b@b.com', 'first_name': 'bob', 'last_name': 'last'},  # Bob's current information minus last name
            follow=True
        )  
        
        self.assertContains(response, 'This field is required.')
        self.assertContains(response, 'Please check the data you entered')
    
    def test_user_cannot_add_numbers_to_first_name(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': 'bob','email': 'b@b.com', 'first_name': 'bob123', 'last_name': 'last'},  # Bob's User data with numbers in the first name
            follow=True
        )  

        self.assertContains(response, 'Numeric digits are not allowed.')
    
    def test_user_cannot_add_numbers_to_last_name(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.post(
            edit_account_url,          
            {'username': 'bob','email': 'b@b.com', 'first_name': 'bob', 'last_name': 'last123'},  # Bob's User data with numbers in the last name
            follow=True
        )  

        self.assertContains(response, 'Numeric digits are not allowed.')

    def test_edit_account_form_prepopulated_with_user_data(self):
        logged_in_user = User.objects.get(pk=2)  # Bob
        self.client.force_login(logged_in_user)

        edit_account_url = reverse('edit_user_account_info', kwargs={'user_pk': 2}) # Bob's edit account page

        response = self.client.get(edit_account_url)

        # Assert that Bob's account information is populating the form upon visiting the page
        self.assertContains(response, 'bob')
        self.assertContains(response, 'bob')
        self.assertContains(response, 'last')
        self.assertContains(response, 'b@b.com')


class TestUserPasswordChange(TestCase):

    fixtures = ['testing_users']

    def test_unauthenticated_user_cannot_access_page(self):
        # Unauthenticated users should not be able to access change_user_password page
        response = self.client.get(reverse('change_user_password', kwargs={'user_pk': 1}), follow=True) 
        # Should redirect to login; which will then redirect to the /user/change_password/1/ page on success.
        self.assertRedirects(response, '/accounts/login/?next=/user/change_password/1/')

    def test_user_cannot_change_other_users_password(self):
        # Users should not be able to change a password that isn't their own
        logged_in_user = User.objects.get(pk=1)  # Alice
        self.client.force_login(logged_in_user)

        response = self.client.get(reverse('change_user_password', kwargs={'user_pk': 2}), follow=True)  # Bob's change password URL

        self.assertTemplateUsed(response, '403.html')  # Assert that Alice gets redirected to 403 template 
        self.assertTemplateUsed(response, 'lmn/base.html')

    def test_user_password_changed_successfully(self):
        # Have to create new user - fixture users' passwords do not pass requirements
        logged_in_user = User.objects.create_user(username='test', password='testPASSword12')
        self.client.force_login(logged_in_user)

        response = self.client.post(
            reverse('change_user_password', kwargs={'user_pk': 4}), 
            {'old_password': 'testPASSword12', 'new_password1': 'Hello-World187', 'new_password2': 'Hello-World187'}, 
            follow=True)
        
        logged_in_user.refresh_from_db()  # Refresh user instance in database

        self.assertTrue(logged_in_user.check_password('Hello-World187'))  # Assert user's password updated 

    def test_user_session_auth_hash_changed_when_password_changes(self):
        logged_in_user = User.objects.create_user(username='test', password='password123')
        self.client.force_login(logged_in_user)

        # Make POST request to change password
        response = self.client.post(
            reverse('change_user_password', kwargs={'user_pk': logged_in_user.pk}),
            {'old_password': 'password123', 'new_password1': 'newpassword123', 'new_password2': 'newpassword123'},
            follow=True
        )

        # Check that the session auth hash is updated
        session = self.client.session
        self.assertTrue(session.get('SESSION_HASH_CHANGED', True))

    def test_user_redirected_to_profile_page_when_password_successfully_changed(self):
        logged_in_user = User.objects.create_user(username='test', password='password123')
        self.client.force_login(logged_in_user)

        # Make POST request to change password
        response = self.client.post(
            reverse('change_user_password', kwargs={'user_pk': logged_in_user.pk}),
            {'old_password': 'password123', 'new_password1': 'newpassword123', 'new_password2': 'newpassword123'},
            follow=True
        )

        self.assertRedirects(response, '/user/profile/4/')

    def test_password_change_template_used(self):

        logged_in_user = User.objects.get(pk=1)
        self.client.force_login(logged_in_user)

        response = self.client.get(reverse('change_user_password', kwargs={'user_pk': 1}), follow=True)

        self.assertTemplateUsed(response, 'lmn/users/change_user_password.html')

    def test_error_message_shown_when_old_password_incorrect(self):
        logged_in_user = User.objects.create_user(username='test', password='password123')
        self.client.force_login(logged_in_user)

        # Make POST request to change password with incorrect old password
        response = self.client.post(
            reverse('change_user_password', kwargs={'user_pk': logged_in_user.pk}),
            {'old_password': 'incorrect_password', 'new_password1': 'newpassword123', 'new_password2': 'newpassword123'},
            follow=True
        )

        self.assertContains(response, 'Your old password was entered incorrectly. Please enter it again.')

    def test_error_message_shown_when_new_passwords_dont_match(self):
        logged_in_user = User.objects.create_user(username='test', password='password123')
        self.client.force_login(logged_in_user)

        # Make POST request to change password with incorrect old password
        response = self.client.post(
            reverse('change_user_password', kwargs={'user_pk': logged_in_user.pk}),
            {'old_password': 'password123', 'new_password1': 'password', 'new_password2': 'mismatched_password'},
            follow=True
        )

        self.assertContains(response, 'The two password fields didn’t match.')

    def test_user_cannot_see_change_password_button_on_other_user_profile(self):
        logged_in_user = User.objects.get(pk=3)  # cat
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))  # Alice's profile
        self.assertNotContains(response, 'Change Password')  # Ensure that user's cannot see button including this text
    
    def test_unauthenticated_user_cannot_see_change_password_button(self):
        # No logged in user. Should not be able to see change password button
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))  # Alice's profile
        self.assertNotContains(response, 'Change Password')  # Ensure that user's cannot see button including this text


class TestNotes(TestCase):
    # Have to add Notes and Users and Show, and also artists and venues because of foreign key constrains in Show
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    def test_latest_notes(self):
        response = self.client.get(reverse('latest_notes'))
        # Should be note 3, then 2, then 1
        context = response.context['notes']
        first, second, third = context[0], context[1], context[2]
        self.assertEqual(first.pk, 3)
        self.assertEqual(second.pk, 2)
        self.assertEqual(third.pk, 1)

    def test_notes_for_show_view(self):
        # Verify correct list of notes shown for a Show, most recent first
        # Show 1 has 2 notes with PK = 2 (most recent) and PK = 1
        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 1}))
        context = response.context['notes']
        first, second = context[0], context[1]
        self.assertEqual(first.pk, 2)
        self.assertEqual(second.pk, 1)

    def test_notes_for_show_when_show_not_found(self):
        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 10000}))
        self.assertEqual(404, response.status_code)

    def test_correct_templates_uses_for_notes(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertTemplateUsed(response, 'lmn/notes/note_list.html')

        response = self.client.get(reverse('note_detail', kwargs={'note_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')

        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/notes/notes_for_show.html')

        # Log someone in
        self.client.force_login(User.objects.first())
        response = self.client.get(reverse('new_note', kwargs={'show_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/notes/new_note.html')
        
    def test_delete_note_render_delete_confirmation_page(self):
        
        self.client.force_login(User.objects.first()) # alice
        response = self.client.post(reverse('delete_note', kwargs={'note_pk': 1}), follow=True)
        self.assertTemplateUsed(response, 'lmn/notes/note_delete_confirmation.html')
        
    def test_delete_note_render_note_detail_if_request_is_get(self):
        
        self.client.force_login(User.objects.first()) # alice
        response = self.client.get(reverse('delete_note', kwargs={'note_pk': 1}), follow=True)
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')
        
    def test_delete_confirmation_render_403_when_trying_to_delete_other_users_note(self):
        
        self.client.force_login(User.objects.first()) # alice
        delete_confirmation_url = reverse('delete_confirmation', kwargs={'note_pk': 2}) # note by bob
        response = self.client.post(
            delete_confirmation_url,
            {'confirm':'yes'}, # confirmed
            follow=True
        )
        self.assertTemplateUsed(response, '403.html') # unable to delete
        
    def test_delete_confirmation_success_when_confirming_to_delete_note_created_by_the_user(self):
        
        self.client.force_login(User.objects.first()) # alice
        delete_confirmation_url = reverse('delete_confirmation', kwargs={'note_pk': 1}) # note by alice
        response = self.client.post(
            delete_confirmation_url,
            {'confirm':'yes'}, # confirmed
            follow=True
        )
        self.assertTemplateUsed(response,'lmn/notes/note_list.html') # note deleted and shows latest notes
        self.assertContains(response,'Your note has been deleted.')
    
    def test_delete_confirmation_renders_note_detail_if_deletion_not_confirmed(self):
        
        self.client.force_login(User.objects.first()) # alice
        delete_confirmation_url = reverse('delete_confirmation', kwargs={'note_pk': 1}) # note by alice
        response = self.client.post(
            delete_confirmation_url,
            {'confirm':'no'}, # confirmed
            follow=True
        )
        self.assertTemplateUsed(response,'lmn/notes/note_detail.html')
        
    def test_delete_confirmation_renders_confirmation_page_if_request_is_get(self):
        
        self.client.force_login(User.objects.first()) # alice
        delete_confirmation_url = reverse('delete_confirmation', kwargs={'note_pk': 1}) # note by alice
        response = self.client.get(
            delete_confirmation_url,
            {'confirm':'yes'}, # confirmed
            follow=True
        )
        self.assertTemplateUsed(response,'lmn/notes/note_delete_confirmation.html')  

    def test_render_403_if_user_edit_note_created_by_others(self):
        
        # Log someone in
        self.client.force_login(User.objects.first()) # alice
        response = self.client.post(reverse('edit_note', kwargs={'note_pk': 2})) # note created by bob
        self.assertTemplateUsed(response, '403.html')
        
    def test_render_note_detail_if_user_edited_form_that_the_user_created_and_form_is_valid(self):
        
        self.client.force_login(User.objects.first()) # alice
        
        edit_note_url = reverse('edit_note', kwargs={'note_pk': 1}) # edit note page
        
        response = self.client.post(
            edit_note_url,
            {'title': 'testing', 'text': 'Testing note created'},
            follow=True
        ) # updating note
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')
        
    def test_render_edit_note_if_user_edited_form_that_the_user_created_and_form_is_valid(self):
        
        self.client.force_login(User.objects.first()) # alice
        
        edit_note_url = reverse('edit_note', kwargs={'note_pk': 1}) # edit note page
        
        response = self.client.post( # invalid form, form can't be blank
            edit_note_url,
            {'title': '', 'text': ''},
            follow=True
        ) # updating note
        self.assertTemplateUsed(response, 'lmn/notes/edit_note.html')
        
    def test_edit_note_success_if_editing_own_note_and_form_is_valid(self):
        
        self.client.force_login(User.objects.first()) # alice
        
        edit_note_url = reverse('edit_note', kwargs={'note_pk': 1}) # edit note page
        
        response = self.client.post(
            edit_note_url,
            {'title': 'testing', 'text': 'Testing note created'},
            follow=True
        ) # updating note
        
        self.assertContains(response,'testing')
        self.assertContains(response,'Testing note created')

class TestAddingNoteForFutureShow(TestCase):
    
    fixtures = ['testing_future_note', 'testing_users']
        
    def test_renders_400_when_trying_to_create_new_note_for_show_in_future(self):
        
        self.client.force_login(User.objects.first()) # alice
        add_new_note_url = reverse('new_note', kwargs={'show_pk': 1}) # for show that is in future
        
        response = self.client.post(
            add_new_note_url,
            {'title': 'Awesome show', 'text': 'Beautiful night'},
            follow=True
        )
        
        self.assertTemplateUsed(response, '400.html')
        
    def test_renders_note_detail_when_adding_valid_note_for_show_in_past(self):
        
        self.client.force_login(User.objects.first()) # alice
        add_new_note_url = reverse('new_note', kwargs={'show_pk': 2}) # show in the past
         
        response = self.client.post(
            add_new_note_url,
            {'title': 'Awesome show', 'text': 'Beautiful night'},
            follow=True
        )
        
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')
        self.assertContains(response, 'Awesome show')
        self.assertContains(response, 'Beautiful night')
        
    def test_renders_new_note_when_adding_invalid_note_for_show_in_past(self):
        
        self.client.force_login(User.objects.first()) # alice
        add_new_note_url = reverse('new_note', kwargs={'show_pk': 2}) # show in the past
         
        response = self.client.post(
            add_new_note_url,
            {'title': '', 'text': 'Beautiful night'},
            follow=True
        )
        
        self.assertTemplateUsed(response, 'lmn/notes/new_note.html')
        
    def test_renders_new_note_form_if_request_is_get(self):
        
        self.client.force_login(User.objects.first()) # alice
        response = self.client.get(reverse('new_note', kwargs={'show_pk': 2})) # show in the past
        
        self.assertTemplateUsed(response, 'lmn/notes/new_note.html')
        
        
        
    


class TestShowsWithMostNotesPage(TestCase):
    # Have to add Notes, Users, and Shows, and also artists and venues because of foreign key constrains in Show
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows_most_notes', 'testing_notes_for_top_shows']

    def test_list_shows_most_notes_correct_template_used(self): 

        response = self.client.get(reverse('shows_with_most_notes'))
        self.assertTemplateUsed(response, 'lmn/shows/shows_with_most_notes.html')
    
    def test_artist_name_displayed_for_show(self):
        # Only one test show, on real site, if there are 10 or more shows, 10 of which have at least one note, there would be 10 artists displayed
        test_top_10_shows = Show(pk=1) 
            
        response = self.client.get(reverse('shows_with_most_notes'), kwargs={'top_10_shows': test_top_10_shows})

        self.assertContains(response, 'REM')

    def test_venue_name_displayed_for_show(self):
        # Only one test show, on real site, if there are 10 or more shows, 10 of which have at least one note, there would be 10 venues displayed
        test_top_10_shows = Show(pk=1) 
            
        response = self.client.get(reverse('shows_with_most_notes'), kwargs={'top_10_shows': test_top_10_shows})

        self.assertContains(response, 'The Turf Club')
    
    def test_note_count_displayed_for_show(self):
        # Only one test show, on real site, if there are 10 or more shows, 10 of which have at least one note, there would be 10 venues displayed
        test_show = Show(pk=1) 
            
        response = self.client.get(reverse('shows_with_most_notes'), kwargs={'top_5_shows': test_show})

        self.assertContains(response, 'Number of <a href="/notes/for_show/1/">notes</a>: 4') # 'notes' is a link to the notes list about given show

    def test_only_shows_with_notes_displayed_on_page(self):
        all_shows = Show.objects.all()  # Contains 5 shows, 4 have notes, 1 does not

        response = self.client.post(reverse('shows_with_most_notes'), shows=all_shows)  # Post to view with all shows from fixture
        top_5_shows = response.context['top_5_shows']  # View should return only 4 shows, each with at least one note

        self.assertEqual(len(top_5_shows), 4)  # Extra show with no notes should not be added to page

    def test_shows_with_most_notes_ordered_by_show_date_desc(self):
        # Make sure that shows are displayed from top to bottom by most recent show date, then number of notes
        shows_with_different_num_notes = Show.objects.all()

        response = self.client.post(reverse('shows_with_most_notes'), shows=shows_with_different_num_notes)  # Post to view with all shows
        top_5_shows = response.context['top_5_shows']
        
        expected_pks = [3, 4, 2 ,1]
        actual_pks = [show.pk for show in top_5_shows]
        self.assertEqual(expected_pks, actual_pks)  # Assert that the view returns shows in the correct order
                         
    def test_header_displays_correct_number_for_num_top_shows(self):
        # Make sure that the number displayed at the top of the page 'Top {num shows} shows with the most notes'
        # For how many shows are displayed 

        all_shows = Show.objects.all() 

        response = self.client.post(reverse('shows_with_most_notes'), shows=all_shows)  # Post to view with all shows from fixture

        self.assertContains(response, 'Top 4 recent shows with the most notes')  # Assert that response contains the correct number displayed


class TestUserAuthentication(TestCase):
    """ Some aspects of registration (e.g. missing data, duplicate username) covered in test_forms """
    """ Currently using much of Django's built-in login and registration system """

    def test_user_registration_logs_user_in(self):
        response = self.client.post(
            reverse('register'), 
            {
                'username': 'sam12345', 
                'email': 'sam@sam.com', 
                'password1': 'feRpj4w4pso3az', 
                'password2': 'feRpj4w4pso3az', 
                'first_name': 'sam', 
                'last_name': 'sam'
            }, 
            follow=True)

        # Assert user is logged in - one way to do it...
        user = auth.get_user(self.client)
        self.assertEqual(user.username, 'sam12345')

        # This works too. Don't need both tests, added this one for reference.
        # sam12345 = User.objects.filter(username='sam12345').first()
        # auth_user_id = int(self.client.session['_auth_user_id'])
        # self.assertEqual(auth_user_id, sam12345.pk)

    def test_user_registration_redirects_to_correct_page(self):
        # TODO If user is browsing site, then registers, once they have registered, they should
        # be redirected to the last page they were at, not the homepage.
        response = self.client.post(
            reverse('register'), 
            {
                'username': 'sam12345', 
                'email': 'sam@sam.com', 
                'password1': 'feRpj4w4pso3az@1!2', 
                'password2': 'feRpj4w4pso3az@1!2', 
                'first_name': 'sam', 
                'last_name': 'sam'
            }, 
            follow=True)
        new_user = authenticate(username='sam12345', password='feRpj4w4pso3az@1!2')
        self.assertRedirects(response, reverse('user_profile', kwargs={"user_pk": new_user.pk}))   
        self.assertContains(response, 'sam12345')  # page has user's username on it


class UserLogoutTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password'
        )

    def test_user_logout_message(self):
        # Force login the user
        self.client.force_login(self.user)

        # Make request to logout url
        response = self.client.get(reverse('logout'), follow=True)

        # Assert the homepage is shown
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lmn/home.html')

        # Assert that the homepage shows the "you are logged out" message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'You have been logged out.')


class TestErrorViews(TestCase):

    def test_404_view(self):
        response = self.client.get('this isnt a url on the site')
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed('404.html')

    def test_404_view_note(self):
        # example view that uses the database, get note with ID 10000
        response = self.client.get(reverse('note_detail', kwargs={'note_pk': 1}))
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed('404.html')

    def test_403_view(self):
        # there are no current views that return 403. When users can edit notes, or edit 
        # their profiles, or do other activities when it must be verified that the 
        # correct user is signed in (else 403) then this test can be written.
        pass 
