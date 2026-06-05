# events/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # ==================== PROFILE URLS ====================
    # ⚠️ IMPORTANT: PUT THESE BEFORE profile/<username> !
    
    # Edit profile (must come BEFORE profile/<username>/)
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
     # View any user's profile (must come AFTER specific URLs!)
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    # My events (separate URL)
    path('my-events/', views.my_events, name='my_events'),
    
   
    
    # ==================== EVENT URLS ====================
    # Create event
    path('create/', views.create_event, name='create_event'),
    
    # Event detail page
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    
    # Edit event
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    
    # Delete event
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # ==================== ATTENDANCE URLS ====================
    # Join event
    path('event/<int:event_id>/join/', views.join_event, name='join_event'),
    
    # Leave event
    path('event/<int:event_id>/leave/', views.leave_event, name='leave_event'),
]