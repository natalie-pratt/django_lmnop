from django import forms
from .models import Note

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.core.validators import RegexValidator


class VenueSearchForm(forms.Form):
    search_name = forms.CharField(label='Venue Name', max_length=200)


class ArtistSearchForm(forms.Form):
    search_name = forms.CharField(label='Artist Name', max_length=200)


class NewNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('title', 'text')


class UserRegistrationForm(UserCreationForm):
    # Do not allow numeric values in first and last names.
    # Source: https://techflow360.com/how-to-perform-django-form-validation-with-regex/
    first_name = forms.CharField(validators=[RegexValidator(r'^[^\d]*$', 'Numeric digits are not allowed.')])
    last_name = forms.CharField(validators=[RegexValidator(r'^[^\d]*$', 'Numeric digits are not allowed.')])

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']

        if not username:
            raise ValidationError('Please enter a username')

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('A user with that username already exists')

        return username

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not first_name:
            raise ValidationError('Please enter your first name')

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not last_name:
            raise ValidationError('Please enter your last name')

        return last_name

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email:
            raise ValidationError('Please enter an email address')

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email address already exists')

        return email

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

        return user


class UserUpdateForm(forms.ModelForm):
    # Do not allow numeric values in first and last names.
    # Source: https://techflow360.com/how-to-perform-django-form-validation-with-regex/
    first_name = forms.CharField(validators=[RegexValidator(r'^[^\d]*$', 'Numeric digits are not allowed.')])
    last_name = forms.CharField(validators=[RegexValidator(r'^[^\d]*$', 'Numeric digits are not allowed.')])

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Taken from Django docs
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists(): # Make sure username doesn't exist in DB already, case-insensitive
            raise ValidationError('A user with that username already exists')                    # Excludes logged in user's current username
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():  # Make sure email doesn't exist in DB already, case-insensitive
            raise ValidationError('A user with that email address already exists')          # Excludes logged in user's current email

        return email
    
    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user
