"""
Tests for the Virtual Workspace Room Booking System.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, time
from .models import Room, Team, Booking, UserProfile


class RoomModelTest(TestCase):
    """Test cases for Room model."""
    
    def setUp(self):
        """Set up test data."""
        self.private_room = Room.objects.create(
            name="Private Room 1",
            room_type="private",
            capacity=1
        )
        self.conference_room = Room.objects.create(
            name="Conference Room 1",
            room_type="conference",
            capacity=5
        )
        self.shared_desk = Room.objects.create(
            name="Shared Desk 1",
            room_type="shared_desk",
            capacity=4
        )
    
    def test_room_creation(self):
        """Test room creation."""
        self.assertEqual(self.private_room.name, "Private Room 1")
        self.assertEqual(self.private_room.room_type, "private")
        self.assertEqual(self.private_room.capacity, 1)
    
    def test_room_validation(self):
        """Test room validation rules."""
        # Test private room with wrong capacity
        with self.assertRaises(ValidationError):
            room = Room(name="Invalid Private", room_type="private", capacity=2)
            room.clean()
        
        # Test conference room with insufficient capacity
        with self.assertRaises(ValidationError):
            room = Room(name="Invalid Conference", room_type="conference", capacity=2)
            room.clean()
        
        # Test shared desk with wrong capacity
        with self.assertRaises(ValidationError):
            room = Room(name="Invalid Shared", room_type="shared_desk", capacity=3)
            room.clean()


class TeamModelTest(TestCase):
    """Test cases for Team model."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(username="user1", email="user1@test.com")
        self.user2 = User.objects.create_user(username="user2", email="user2@test.com")
        self.child_user = User.objects.create_user(username="child", email="child@test.com")
        
        # Create profiles
        UserProfile.objects.create(user=self.user1, age=25)
        UserProfile.objects.create(user=self.user2, age=30)
        UserProfile.objects.create(user=self.child_user, age=8)
        
        self.team = Team.objects.create(name="Test Team")
        self.team.members.add(self.user1, self.user2, self.child_user)
    
    def test_team_member_counts(self):
        """Test team member count calculations."""
        self.assertEqual(self.team.get_total_member_count(), 3)
        self.assertEqual(self.team.get_effective_member_count(), 2)  # Excluding child


class BookingModelTest(TestCase):
    """Test cases for Booking model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@test.com")
        UserProfile.objects.create(user=self.user, age=25)
        
        self.team = Team.objects.create(name="Test Team")
        self.team.members.add(self.user)
        
        self.private_room = Room.objects.create(
            name="Private Room 1",
            room_type="private",
            capacity=1
        )
        
        self.conference_room = Room.objects.create(
            name="Conference Room 1",
            room_type="conference",
            capacity=5
        )
    
    def test_booking_creation(self):
        """Test booking creation."""
        booking = Booking.objects.create(
            room=self.private_room,
            user=self.user,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        
        self.assertEqual(booking.room, self.private_room)
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, 'active')
    
    def test_booking_validation(self):
        """Test booking validation rules."""
        # Test invalid time slot (outside 9-6)
        with self.assertRaises(ValidationError):
            booking = Booking(
                room=self.private_room,
                user=self.user,
                date=date.today(),
                start_time=time(8, 0),
                end_time=time(9, 0)
            )
            booking.clean()
        
        # Test non-hourly slot
        with self.assertRaises(ValidationError):
            booking = Booking(
                room=self.private_room,
                user=self.user,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(10, 30)
            )
            booking.clean()
        
        # Test team booking private room
        with self.assertRaises(ValidationError):
            booking = Booking(
                room=self.private_room,
                team=self.team,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0)
            )
            booking.clean()
    
    def test_booking_cancellation(self):
        """Test booking cancellation."""
        booking = Booking.objects.create(
            room=self.private_room,
            user=self.user,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        
        self.assertEqual(booking.status, 'active')
        booking.cancel()
        self.assertEqual(booking.status, 'cancelled')
