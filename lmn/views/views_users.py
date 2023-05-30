from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from ..forms import UserRegistrationForm, UserUpdateForm
from ..models import Note


def user_profile(request, user_pk):
    """ Get user profile for any user on the site. 
    Any user may view any other user's profile. 
    """
    user = User.objects.get(pk=user_pk)
    usernotes = Note.objects.filter(user=user.pk).order_by('-posted_date')
    return render(request, 'lmn/users/user_profile.html', {'user_profile': user, 'notes': usernotes, 'messages': messages.get_messages(request)})


@login_required
def my_user_profile(request):
    """ Get the currently logged-in user's profile """
    return redirect('user_profile', user_pk=request.user.pk)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, **kwargs):
    """ Display message to User upon logout """
    messages.add_message(request, messages.INFO, 'You have been logged out.', extra_tags='goodbye-message')  # extra_tags = CSS class


@login_required
def edit_user_account_info(request, user_pk):
    """ Handles updating currently logged in user account information.
    Can update username, first name, last name, and email. 
    Redirects to profile page if update is successful. """
    user = User.objects.get(pk=user_pk)  # Get currently logged in User
    form = UserUpdateForm(instance=user)  # Populate new form with User's current information

    if request.user != user: # Ensure that user is authenticated to update the account
        return render(request, '403.html')
    
    if request.method == 'POST':
        # If POST request, populate the form with the newly entered data for the User
        form = UserUpdateForm(request.POST, instance=user)  

        if form.is_valid():
            form.save()  # Save the new data to the logged in User object if form is valid
            # Log success message to template
            messages.success(request, 'Your account information has been successfully updated!', extra_tags='success-message' )  # extra_tags = CSS class
            return redirect('user_profile', user_pk) # If all is successful, return to profile page
        else:
            messages.add_message(request, messages.INFO, 'Please check the data you entered')
            # If the form isn't valid, return a message and the form to the edit_user_account_info template
            return render(request, 'lmn/users/edit_user_account_info.html', {'form': form})

    return render(request, 'lmn/users/edit_user_account_info.html', {'form': form})


@login_required
def change_user_password(request, user_pk):
    """ Handles changing logged-in user's password. """
    user = User.objects.get(pk=user_pk)
    form = PasswordChangeForm(user=user)

    if request.user != user:  # Ensure that user is authenticated to change the password
        return render(request, '403.html')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Update user session hash for security
            messages.success(request, 'Your password was successfully updated!', extra_tags='success-message')  # extra_tags = CSS class
            return redirect('user_profile', user_pk=request.user.pk)

    return render(request, 'lmn/users/change_user_password.html', {'form': form})


def register(request):
    """ Handles user registration flow.

    GET request - show a user registration form.
    POST request - register a new user
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            if user:
                login(request, user)
                return redirect('user_profile', user_pk=request.user.pk)
            else:
                messages.add_message(request, messages.ERROR, 'Unable to log in new user')
        else:
            messages.add_message(request, messages.INFO, 'Please check the data you entered')
            # Include the invalid form, which will have error messages added to it. 
            # The error messages will be displayed by the template.
            return render(request, 'registration/register.html', {'form': form, 'messages': messages.get_messages(request)})

    form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form, 'messages': messages.get_messages(request)})
