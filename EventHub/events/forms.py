# events/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, EventCategory, UserProfile


# Form 1: User Registration
class UserRegistrationForm(UserCreationForm):
    """Custom signup form with extra fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_email(self):
        """Check if email already exists"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered!")
        return email
    
    def clean_username(self):
        """Check if username already exists"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken!")
        return username

# Form 2: User Profile Update
class UserProfileForm(forms.ModelForm):
    """Form to update user profile"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'year', 'branch', 'phone']
        
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }


# Form 3: Create/Edit Event
class EventForm(forms.ModelForm):
    """Form to create or edit events"""
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'date', 'time', 
                  'duration_hours', 'location', 'max_attendees', 'cover_image']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your event...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # HTML5 date picker
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'  # HTML5 time picker
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 24
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where will it be held?'
            }),
            'max_attendees': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0 for unlimited'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_date(self):
        """Validate date is in future"""
        from datetime import date
        date_value = self.cleaned_data.get('date')
        if date_value < date.today():
            raise forms.ValidationError("Event date must be in the future!")
        return date_value