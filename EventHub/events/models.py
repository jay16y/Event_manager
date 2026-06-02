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


# Model 3: Event (Main model)
class Event(models.Model):
    """Campus events that users can create and join"""
    
    # Basic Info
    title = models.CharField(max_length=200)
    # max_length=200 means max 200 characters
    
    description = models.TextField()
    # TextField allows long text
    
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True
    )
    # ForeignKey means event belongs to ONE category
    # on_delete=models.SET_NULL means if category deleted, it becomes null
    
    # Creator Info
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    # related_name='created_events' means we can do:
    # user.created_events.all() to get all events they created
    
    # Date/Time Info
    date = models.DateField()
    # DateField stores just the date (no time)
    
    time = models.TimeField()
    # TimeField stores just the time
    
    duration_hours = models.IntegerField(default=1)
    # IntegerField for whole numbers
    
    # Location
    location = models.CharField(max_length=300)
    # Where the event happens
    
    # Capacity
    max_attendees = models.IntegerField(
        default=0,
        help_text="0 means unlimited"
    )
    # 0 = unlimited spots
    
    # Image
    cover_image = models.ImageField(
        upload_to='event_images/',
        blank=True,
        null=True
    )
    # Event poster/cover image
    
    # Status
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming'
    )
    
    # Attendees (Many-to-Many)
    attendees = models.ManyToManyField(
        User,
        through='Attendance',
        related_name='attending_events',
        blank=True
    )
    # ManyToManyField means many users can join one event
    # and user can join many events
    # through='Attendance' uses Attendance model to track join details
    # related_name allows: user.attending_events.all()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # auto_now=True means it updates every time event is modified
    
    def __str__(self):
        return self.title
    
    def attendees_count(self):
        """Return number of attendees"""
        return self.attendees.count()
    
    def is_full(self):
        """Check if event is at capacity"""
        if self.max_attendees == 0:
            return False
        return self.attendees_count() >= self.max_attendees
    
    def is_creator(self, user):
        """Check if user is the creator"""
        return self.creator == user
    
    def is_attending(self, user):
        """Check if user is attending"""
        return self.attendees.filter(id=user.id).exists()
    
    class Meta:
        ordering = ['-date']  # Show newest events first
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['category']),
        ]


# Model 4: Attendance (Track who joins what)
class Attendance(models.Model):
    """Track attendance details for events"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Which user
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # Which event
    
    joined_at = models.DateTimeField(auto_now_add=True)
    # When did they join
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('interested', 'Interested'),
            ('going', 'Going'),
            ('attended', 'Attended'),
            ('cancelled', 'Cancelled'),
        ],
        default='going'
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
    
    class Meta:
        unique_together = ['user', 'event']
        # This prevents user from joining same event twice
        ordering = ['-joined_at']

# Model 5: Notification (Optional but good)
class Notification(models.Model):
    """Notify users about event updates"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    message = models.TextField()
    
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('new_event', 'New Event'),
            ('new_attendee', 'New Attendee'),
            ('event_cancelled', 'Event Cancelled'),
            ('event_updated', 'Event Updated'),
        ]
    )
    
    is_read = models.BooleanField(default=False)
    # BooleanField is true/false
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"
    
    class Meta:
        ordering = ['-created_at']