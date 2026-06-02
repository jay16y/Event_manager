# events/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Model 1: EventCategory
class EventCategory(models.Model):
    """Categories like Sports, Cultural, Technical, etc."""
    
    name = models.CharField(max_length=100, unique=True)
    # unique=True means no two categories can have same name
    
    description = models.TextField(blank=True, null=True)
    # blank=True means it's optional in forms
    # null=True means it can be empty in database
    
    icon = models.CharField(max_length=50, default="📌")
    # Just emoji for now, can be image path later
    
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now_add=True means it sets current time when created
    
    def __str__(self):
        # This is what shows in admin panel
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        # Fixes plural spelling in admin


# Model 2: UserProfile (Extra user info)
class UserProfile(models.Model):
    """Extra information about users beyond Django's User model"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # OneToOneField means each user has exactly ONE profile
    # on_delete=models.CASCADE means if user is deleted, profile is deleted too
    
    bio = models.TextField(blank=True, null=True, max_length=500)
    # Short bio about the user
    
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='profile_pictures/default.jpg',
        blank=True
    )
    # upload_to='profile_pictures/' creates a folder for images
    # default is fallback if no image uploaded
    
    year = models.CharField(
        max_length=20,
        choices=[
            ('1st', '1st Year'),
            ('2nd', '2nd Year'),
            ('3rd', '3rd Year'),
            ('4th', '4th Year'),
            ('other', 'Other'),
        ],
        default='1st'
    )
    # choices limits what can be selected
    
    branch = models.CharField(
        max_length=100,
        choices=[
            ('CSE', 'Computer Science'),
            ('ECE', 'Electronics'),
            ('ME', 'Mechanical'),
            ('CE', 'Civil'),
            ('other', 'Other'),
        ],
        default='CSE'
    )
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


