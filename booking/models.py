"""
Models for the Virtual Workspace Room Booking System.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time


class Team(models.Model):
    """Team model for conference room bookings."""
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(User, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_effective_member_count(self):
        """Get member count excluding children (age < 10)."""
        return self.members.filter(profile__age__gte=10).count()
    
    def get_total_member_count(self):
        """Get total member count including children."""
        return self.members.count()


class UserProfile(models.Model):
    """Extended user profile with age information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.user.username} (age: {self.age})"


class Room(models.Model):
    """Room model with different types and capacities."""
    
    ROOM_TYPES = [
        ('private', 'Private Room'),
        ('conference', 'Conference Room'),
        ('shared_desk', 'Shared Desk'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"
    
    def clean(self):
        """Validate room capacity based on type."""
        if self.room_type == 'private' and self.capacity != 1:
            raise ValidationError("Private rooms must have capacity of 1")
        elif self.room_type == 'conference' and self.capacity < 3:
            raise ValidationError("Conference rooms must have capacity of at least 3")
        elif self.room_type == 'shared_desk' and self.capacity != 4:
            raise ValidationError("Shared desks must have capacity of 4")


class Booking(models.Model):
    """Booking model with all business rules implemented."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Booking details
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    
    # Time slot
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['room', 'date', 'start_time', 'end_time', 'status']
    
    def __str__(self):
        booking_type = f"Team: {self.team.name}" if self.team else f"User: {self.user.username}"
        return f"{self.room.name} - {self.date} {self.start_time}-{self.end_time} ({booking_type})"
    
    def clean(self):
        """Validate booking constraints."""
        # Validate that either user or team is provided, but not both
        if not self.user and not self.team:
            raise ValidationError("Either user or team must be provided")
        if self.user and self.team:
            raise ValidationError("Cannot book for both user and team simultaneously")
        
        # Validate time slot (9 AM to 6 PM, hourly)
        if self.start_time < time(9, 0) or self.end_time > time(18, 0):
            raise ValidationError("Booking time must be between 9 AM and 6 PM")
        
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Validate hourly slots
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if (end_minutes - start_minutes) != 60:
            raise ValidationError("Booking must be exactly 1 hour")
        
        # Validate room type constraints
        if self.room.room_type == 'private' and self.team:
            raise ValidationError("Private rooms can only be booked by individual users")
        
        if self.room.room_type == 'conference' and self.user:
            raise ValidationError("Conference rooms can only be booked by teams")
        
        if self.room.room_type == 'conference' and self.team:
            if self.team.get_effective_member_count() < 3:
                raise ValidationError("Conference rooms require teams with at least 3 members (excluding children)")
        
        # Validate shared desk capacity
        if self.room.room_type == 'shared_desk':
            # Check current bookings for this slot
            existing_bookings = Booking.objects.filter(
                room=self.room,
                date=self.date,
                start_time=self.start_time,
                end_time=self.end_time,
                status='active'
            ).exclude(id=self.id)
            
            current_occupancy = sum(
                booking.team.get_total_member_count() if booking.team else 1
                for booking in existing_bookings
            )
            
            new_occupancy = self.team.get_total_member_count() if self.team else 1
            
            if current_occupancy + new_occupancy > self.room.capacity:
                raise ValidationError(f"Shared desk capacity exceeded. Current: {current_occupancy}, Adding: {new_occupancy}, Max: {self.room.capacity}")
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def cancel(self):
        """Cancel the booking."""
        self.status = 'cancelled'
        self.save()
    
    @classmethod
    def get_available_rooms(cls, date, start_time, end_time, room_type=None):
        """Get available rooms for a specific time slot."""
        # Get all rooms of the specified type
        rooms = Room.objects.all()
        if room_type:
            rooms = rooms.filter(room_type=room_type)
        
        available_rooms = []
        
        for room in rooms:
            # Check for overlapping bookings
            overlapping_bookings = cls.objects.filter(
                room=room,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='active'
            )
            
            if not overlapping_bookings.exists():
                # For shared desks, check capacity
                if room.room_type == 'shared_desk':
                    current_occupancy = sum(
                        booking.team.get_total_member_count() if booking.team else 1
                        for booking in overlapping_bookings
                    )
                    if current_occupancy < room.capacity:
                        available_rooms.append(room)
                else:
                    available_rooms.append(room)
        
        return available_rooms
