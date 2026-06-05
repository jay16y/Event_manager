# events/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from .models import Event, EventCategory, UserProfile, Attendance, Notification
from .forms import UserRegistrationForm, EventForm, UserProfileForm


# ==================== AUTHENTICATION VIEWS ====================

def register(request):
    """Handle user registration/signup"""
    
    if request.method == 'POST':
        # User submitted the form
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Form data is correct
            user = form.save()  # Save to database
            
            # Create UserProfile for new user
            UserProfile.objects.create(user=user)
            
            # Show success message
            messages.success(request, "Account created! Please login.")
            return redirect('login')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET request - show empty form
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handle user login"""
    
    if request.user.is_authenticated:
        # Already logged in, go to home
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if credentials are correct
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('home')
        else:
            # Login failed
            messages.error(request, "Invalid username or password")
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect('home')


# ==================== EVENT VIEWS ====================

def home(request):
    """Display the homepage with a list of events"""
    
    # Search functionality - read 'search' param to match template input name
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-date')
    
    events = Event.objects.all()
    
    # Apply search filter
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        ).distinct()
    
    # Apply category filter
    if category_id:
        events = events.filter(category_id=category_id)
    
    # Apply sort ordering
    if sort_by in ['date', '-date', 'title']:
        events = events.order_by(sort_by)

    for event in events:
        if event.max_attendees > 0:
            event.percentage = (event.attendees_count() / event.max_attendees) * 100
        else:
            event.percentage = 0
            
    categories = EventCategory.objects.all()
    
    context = {
        'events': events,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_sort': sort_by,
    }
    return render(request, 'events/home.html', context)


@login_required(login_url='login')
def create_event(request):
    """Create a new event (requires 'can_create_event' permission)"""
    
    # Check if user has permission to create events
    if not request.user.has_perm('events.can_create_event'):
        messages.error(request, "You don't have permission to create events. Contact an admin to get access.")
        return redirect('home')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        
        if form.is_valid():
            event = form.save(commit=False)
            # commit=False means don't save yet
            
            event.creator = request.user
            # Set the creator as current user
            
            event.save()
            # Now save to database
            
            messages.success(request, "Event created successfully!")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    return render(request, 'events/create_event.html', {'form': form})


def event_detail(request, event_id):
    """Show details of a specific event"""
    
    event = get_object_or_404(Event, id=event_id)
    # get_object_or_404 shows 404 page if event not found
    
    is_creator = event.creator == request.user
    is_attending = request.user.is_authenticated and event.is_attending(request.user)
    can_join = not is_attending and not event.is_full()
    
    context = {
        'event': event,
        'is_creator': is_creator,
        'is_attending': is_attending,
        'can_join': can_join,
    }
    
    return render(request, 'events/event_detail.html', context)


@login_required(login_url='login')
def edit_event(request, event_id):
    """Edit an event (creator only)"""
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is creator
    if event.creator != request.user:
        messages.error(request, "You can only edit your own events!")
        return redirect('event_detail', event_id=event_id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        # instance=event means update existing event, not create new
        
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully!")
            return redirect('event_detail', event_id=event_id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required(login_url='login')
def delete_event(request, event_id):
    """Delete an event (creator only)"""
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    if event.creator != request.user:
        messages.error(request, "You can only delete your own events!")
        return redirect('event_detail', event_id=event_id)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully!")
        return redirect('home')
    
    return render(request, 'events/confirm_delete.html', {'event': event})


# ==================== ATTENDANCE VIEWS ====================

@login_required(login_url='login')
def join_event(request, event_id):
    """Join an event"""
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check if event is full
    if event.is_full():
        messages.error(request, "This event is full!")
        return redirect('event_detail', event_id=event_id)
    
    # Check if already attending
    if event.is_attending(request.user):
        messages.error(request, "You're already attending this event!")
        return redirect('event_detail', event_id=event_id)
    
    # Add user to attendees
    Attendance.objects.create(
        user=request.user,
        event=event,
        status='going'
    )
    
    messages.success(request, f"You joined {event.title}!")
    
    # Notify event creator
    Notification.objects.create(
        user=event.creator,
        event=event,
        message=f"{request.user.first_name} joined your event!",
        notification_type='new_attendee'
    )
    
    return redirect('event_detail', event_id=event_id)


@login_required(login_url='login')
def leave_event(request, event_id):
    """Leave an event"""
    
    event = get_object_or_404(Event, id=event_id)
    
    # Find and delete attendance record
    attendance = Attendance.objects.filter(
        user=request.user,
        event=event
    ).first()
    
    if attendance:
        attendance.delete()
        messages.success(request, "You left the event!")
    
    return redirect('event_detail', event_id=event_id)


# ==================== PROFILE VIEWS ====================

@login_required(login_url='login')
def my_events(request):
    """Show user's events (created and attending)"""
    
    # Get profile
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Events created by user
    created_events = Event.objects.filter(creator=request.user)
    
    # Events user is attending
    attending_events = Event.objects.filter(
        attendees=request.user
    )
    
    context = {
        'profile': profile,
        'created_events': created_events,
        'attending_events': attending_events,
    }
    
    return render(request, 'events/my_events.html', context)


def user_profile(request, username):
    """View user's public profile"""
    
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    
    created_events = Event.objects.filter(creator=user)
    attending_events = Event.objects.filter(attendees=user)
    
    context = {
        'user': user,
        'profile': profile,
        'created_events': created_events,
        'attending_events': attending_events,
    }
    
    return render(request, 'events/user_profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    """Edit user's profile"""
    
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('my_events')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'events/edit_profile.html', {'form': form})