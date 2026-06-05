# events/admin.py - FIXED VERSION

from django.contrib import admin
from .models import EventCategory, UserProfile, Event, Attendance, Notification

# ==================== EventCategory Admin ====================
@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    """Admin for managing event categories"""
    
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'icon', 'description')
        }),
    )


# ==================== UserProfile Admin ====================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for managing user profiles"""
    
    list_display = ['user', 'year', 'branch', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__email']
    list_filter = ['year', 'branch', 'created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('bio', 'profile_picture', 'phone')
        }),
        ('Education', {
            'fields': ('year', 'branch')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'created_at']
        return ['created_at']


# ==================== Event Admin ====================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for managing events"""
    
    list_display = ['title', 'category', 'creator', 'date', 'attendees_count', 'status', 'created_at']
    search_fields = ['title', 'description', 'creator__username', 'location']
    list_filter = ['category', 'status', 'date', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'attendees_count']
    
    # REMOVED: filter_horizontal because we use through='Attendance'
    # REMOVED: attendees from fieldsets because it's managed through Attendance model
    
    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'category', 'status')
        }),
        ('Creator', {
            'fields': ('creator',),
            'classes': ('collapse',)
        }),
        ('Date & Time', {
            'fields': ('date', 'time', 'duration_hours')
        }),
        ('Location & Capacity', {
            'fields': ('location', 'max_attendees')
        }),
        ('Media', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'updated_at', 'attendees_count', 'creator']
        return ['created_at', 'updated_at', 'attendees_count']
    
    def attendees_count(self, obj):
        """Display number of attendees"""
        return obj.attendees.count()
    attendees_count.short_description = "Attendee Count"


# ==================== Attendance Admin ====================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin for managing attendance - USE THIS to add attendees to events"""
    
    list_display = ['user', 'event', 'status', 'joined_at']
    search_fields = ['user__username', 'event__title']
    list_filter = ['status', 'joined_at']
    readonly_fields = ['joined_at']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('user', 'event', 'status')
        }),
        ('Timestamp', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'event', 'joined_at']
        return ['joined_at']


# ==================== Notification Admin ====================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for managing notifications"""
    
    list_display = ['user', 'notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']
    list_filter = ['notification_type', 'is_read', 'created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'message', 'notification_type')
        }),
        ('Event', {
            'fields': ('event',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['created_at', 'user', 'message']
        return ['created_at']