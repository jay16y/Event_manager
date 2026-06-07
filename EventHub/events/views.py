# events/views.py
import random
import time

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from .models import Event, EventCategory, UserProfile, Attendance, Notification, PasswordResetOTP
from .forms import UserRegistrationForm, EventForm, UserProfileForm


# ==================== AUTHENTICATION VIEWS ====================

def register(request):
    """Handle user registration/signup with email OTP verification"""
    
    if request.method == 'POST':
        # User submitted the form
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Don't create user yet - verify email first
            otp_code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            
            # Send OTP to email FIRST (before modifying session)
            try:
                send_mail(
                    subject='EventHub - Verify Your Email',
                    message=(
                        f'Hello {form.cleaned_data["first_name"]},\n\n'
                        f'Your email verification OTP is: {otp_code}\n\n'
                        f'This OTP will expire in 10 minutes.\n\n'
                        f'If you did not sign up on EventHub, please ignore this email.\n\n'
                        f'- EventHub Team'
                    ),
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception:
                messages.error(request, "Failed to send verification email. Please check your email and try again.")
                return render(request, 'accounts/register.html', {'form': form})
            
            # Email sent successfully - now store data in session
            request.session['signup_data'] = {
                'email': email,
                'username': form.cleaned_data['username'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'password': form.cleaned_data['password1'],
            }
            request.session['signup_otp'] = otp_code
            request.session['signup_otp_time'] = time.time()
            
            messages.success(request, f"Verification OTP sent to {email}")
            return redirect('verify_signup_email')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET request - show empty form
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_signup_email(request):
    """Verify email OTP during signup - only creates account after verification"""
    
    signup_data = request.session.get('signup_data')
    if not signup_data:
        messages.error(request, "Please fill the signup form first.")
        return redirect('register')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        stored_otp = request.session.get('signup_otp')
        otp_time = request.session.get('signup_otp_time', 0)
        
        # Check OTP expiry (10 minutes)
        if time.time() - otp_time > 600:
            # Clean up expired session data
            for key in ['signup_data', 'signup_otp', 'signup_otp_time']:
                request.session.pop(key, None)
            messages.error(request, "OTP has expired. Please sign up again.")
            return redirect('register')
        
        if otp_entered == stored_otp:
            # OTP verified! Now create the user account
            user = User.objects.create_user(
                username=signup_data['username'],
                email=signup_data['email'],
                password=signup_data['password'],
                first_name=signup_data['first_name'],
                last_name=signup_data['last_name'],
            )
            
            # Create UserProfile
            UserProfile.objects.create(user=user)
            
            # Clean up session
            for key in ['signup_data', 'signup_otp', 'signup_otp_time']:
                request.session.pop(key, None)
            
            messages.success(request, "Email verified! Account created successfully. Please login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    
    return render(request, 'accounts/verify_signup_email.html', {
        'email': signup_data['email']
    })


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


# ==================== PASSWORD RESET VIEWS ====================

def forgot_password(request):
    """Step 1: Enter email to receive OTP"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
            return render(request, 'accounts/forgot_password.html')
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Invalidate any previous unused OTPs for this user
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Save new OTP
        PasswordResetOTP.objects.create(user=user, otp=otp_code)
        
        # Send OTP via email
        try:
            send_mail(
                subject='EventHub - Password Reset OTP',
                message=(
                    f'Hello {user.first_name},\n\n'
                    f'Your OTP for password reset is: {otp_code}\n\n'
                    f'This OTP will expire in 10 minutes.\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'- EventHub Team'
                ),
                from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, f"OTP has been sent to {email}")
        except Exception:
            messages.error(request, "Failed to send email. Please try again later.")
            return render(request, 'accounts/forgot_password.html')
        
        # Store email in session for next steps
        request.session['reset_email'] = email
        return redirect('verify_otp')
    
    return render(request, 'accounts/forgot_password.html')


def verify_otp(request):
    """Step 2: Verify the OTP sent to email"""
    
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Please enter your email first.")
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, otp=otp_entered, is_used=False
            ).latest('created_at')
            
            if otp_obj.is_expired():
                messages.error(request, "OTP has expired. Please request a new one.")
                return redirect('forgot_password')
            
            # Mark OTP as used
            otp_obj.is_used = True
            otp_obj.save()
            
            # Allow password reset
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')
            
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            messages.error(request, "Invalid OTP. Please try again.")
    
    return render(request, 'accounts/verify_otp.html', {'email': email})


def reset_password(request):
    """Step 3: Set new password after OTP verification"""
    
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Please verify your OTP first.")
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if password != confirm_password:
            messages.error(request, "Passwords don't match!")
            return render(request, 'accounts/reset_password.html')
        
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'accounts/reset_password.html')
        
        try:
            user = User.objects.get(id=user_id)
            user.set_password(password)
            user.save()
            
            # Clean up session
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'reset_user_id' in request.session:
                del request.session['reset_user_id']
            
            messages.success(request, "Password reset successfully! Please login with your new password.")
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('forgot_password')
    
    return render(request, 'accounts/reset_password.html')