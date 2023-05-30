from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError

from ..models import Show, Note


class TestUser(TestCase):

    def test_create_user_duplicate_username_fails(self):
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()

        user2 = User(username='bob', email='another_bob@bob.com', first_name='bob', last_name='bob')
        with self.assertRaises(IntegrityError):
            user2.save()

    def test_create_user_duplicate_email_fails(self):
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()

        user2 = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        with self.assertRaises(IntegrityError):
            user2.save()


class TestShow(TestCase):

    fixtures = ['testing_users', 'testing_artists','testing_venues','testing_shows_most_notes', 'testing_notes_for_top_shows']

    def test_shows_have_correct_note_count_note_created_or_deleted(self):
        # Ensure that a show has the correct note count when a note is created or deleted for that show
        test_show = Show.objects.get(pk=1)  # Show should have 4 notes at start
        test_user = User.objects.get(pk=1)
        title = 'Test'
        text = 'Test text'
        posted_date = '2017-02-12T19:30:00-00:00'

        test_note = Note.objects.create(show=test_show, user=test_user, title=title, text=text, posted_date=posted_date) 

        self.assertEqual(test_show.note_count, 5)  # Note count should be 5 after creating a note for show with 4 notes

        test_note.delete()
        
        self.assertEqual(test_show.note_count, 4)  # Note count should go back down to 4 if one note is deleted

    def test_shows_have_correct_note_count_no_notes(self):
        test_show = Show.objects.get(pk=5)

        self.assertEqual(test_show.note_count, 0)

    def test_shows_have_correct_note_count_1_note(self):
        test_show = Show.objects.get(pk=3)

        self.assertEqual(test_show.note_count, 1)

    def test_shows_have_correct_note_count_lots_of_notes(self):
        test_show = Show.objects.get(pk=5)
        test_user = User.objects.get(pk=1)
        title = 'Test'
        text = 'Test text'
        posted_date = '2017-02-12T19:30:00-00:00'

        for i in range(100):
            Note.objects.create(show=test_show, user=test_user, title=title, text=text, posted_date=posted_date) 

        self.assertEqual(test_show.note_count, 100)
        