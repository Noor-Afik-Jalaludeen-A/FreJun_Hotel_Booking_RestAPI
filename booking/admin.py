"""
Admin configuration for the booking app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Room, Team, Booking, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    """Custom user admin with profile inline."""
    inlines = (UserProfileInline,)


class RoomAdmin(admin.ModelAdmin):
    """Admin for Room model."""
    list_display = ['name', 'room_type', 'capacity', 'created_at']
    list_filter = ['room_type', 'created_at']
    search_fields = ['name']
    ordering = ['name']


class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""
    list_display = ['name', 'get_member_count', 'get_effective_member_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    filter_horizontal = ['members']
    
    def get_member_count(self, obj):
        """Get total member count."""
        return obj.get_total_member_count()
    get_member_count.short_description = 'Total Members'
    
    def get_effective_member_count(self, obj):
        """Get effective member count (excluding children)."""
        return obj.get_effective_member_count()
    get_effective_member_count.short_description = 'Effective Members'


class BookingAdmin(admin.ModelAdmin):
    """Admin for Booking model."""
    list_display = ['room', 'get_booking_type', 'get_booking_name', 'date', 'start_time', 'end_time', 'status', 'created_at']
    list_filter = ['status', 'date', 'room__room_type', 'created_at']
    search_fields = ['room__name', 'user__username', 'team__name']
    date_hierarchy = 'date'
    ordering = ['-created_at']
    
    def get_booking_type(self, obj):
        """Get booking type (user or team)."""
        return 'Team' if obj.team else 'User'
    get_booking_type.short_description = 'Type'
    
    def get_booking_name(self, obj):
        """Get booking name (user or team name)."""
        return obj.team.name if obj.team else obj.user.username
    get_booking_name.short_description = 'Booked By'


# Register models
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Booking, BookingAdmin)
