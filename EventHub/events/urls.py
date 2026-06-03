# events/urls.py

from django.urls import path
from . import views

# URL patterns for events app
urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Events
    path('create/', views.create_event, name='create_event'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # Attendance
    path('event/<int:event_id>/join/', views.join_event, name='join_event'),
    path('event/<int:event_id>/leave/', views.leave_event, name='leave_event'),
    
    # Profile
    path('my-events/', views.my_events, name='my_events'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]