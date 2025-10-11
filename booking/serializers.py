"""
Serializers for the Virtual Workspace Room Booking System.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Team, Booking, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    
    class Meta:
        model = UserProfile
        fields = ['age']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user with profile information."""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for team."""
    members = UserSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    effective_member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'members', 'member_count', 'effective_member_count', 'created_at']
    
    def get_member_count(self, obj):
        """Get total member count including children."""
        return obj.get_total_member_count()
    
    def get_effective_member_count(self, obj):
        """Get member count excluding children (age < 10)."""
        return obj.get_effective_member_count()


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for room."""
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'room_type', 'capacity', 'created_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings."""
    room_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    team_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Booking
        fields = ['room_id', 'user_id', 'team_id', 'date', 'start_time', 'end_time']
    
    def validate(self, data):
        """Validate booking data."""
        # Check that either user_id or team_id is provided
        if not data.get('user_id') and not data.get('team_id'):
            raise serializers.ValidationError("Either user_id or team_id must be provided")
        
        if data.get('user_id') and data.get('team_id'):
            raise serializers.ValidationError("Cannot provide both user_id and team_id")
        
        # Validate room exists
        try:
            room = Room.objects.get(id=data['room_id'])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found")
        
        # Validate user/team exists
        if data.get('user_id'):
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                raise serializers.ValidationError("User not found")
        else:
            try:
                team = Team.objects.get(id=data['team_id'])
            except Team.DoesNotExist:
                raise serializers.ValidationError("Team not found")
        
        return data
    
    def create(self, validated_data):
        """Create a new booking."""
        room_id = validated_data.pop('room_id')
        user_id = validated_data.pop('user_id', None)
        team_id = validated_data.pop('team_id', None)
        
        room = Room.objects.get(id=room_id)
        user = User.objects.get(id=user_id) if user_id else None
        team = Team.objects.get(id=team_id) if team_id else None
        
        # Check for existing bookings by the same user/team
        existing_booking = Booking.objects.filter(
            date=validated_data['date'],
            start_time=validated_data['start_time'],
            end_time=validated_data['end_time'],
            status='active'
        )
        
        if user:
            existing_booking = existing_booking.filter(user=user)
        else:
            existing_booking = existing_booking.filter(team=team)
        
        if existing_booking.exists():
            raise serializers.ValidationError("User/Team already has a booking for this time slot")
        
        # Create the booking
        booking = Booking.objects.create(
            room=room,
            user=user,
            team=team,
            **validated_data
        )
        
        return booking


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for booking details."""
    room = RoomSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'room', 'user', 'team', 'date', 'start_time', 'end_time', 
                 'status', 'created_at', 'updated_at']


class AvailableRoomsSerializer(serializers.Serializer):
    """Serializer for available rooms query."""
    slot = serializers.CharField(help_text="Time slot in format 'HH-HH' (e.g., '10-11')")
    room_type = serializers.ChoiceField(
        choices=Room.ROOM_TYPES,
        required=False,
        help_text="Filter by room type"
    )
    
    def validate_slot(self, value):
        """Validate slot format."""
        try:
            start_hour, end_hour = value.split('-')
            start_hour = int(start_hour)
            end_hour = int(end_hour)
            
            if start_hour < 9 or end_hour > 18:
                raise serializers.ValidationError("Time slot must be between 9 and 18")
            
            if end_hour - start_hour != 1:
                raise serializers.ValidationError("Time slot must be exactly 1 hour")
            
            return value
        except ValueError:
            raise serializers.ValidationError("Invalid slot format. Use 'HH-HH' (e.g., '10-11')")


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for booking list with pagination."""
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    booking_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['id', 'room_name', 'room_type', 'booking_type', 'user_name', 
                 'team_name', 'date', 'start_time', 'end_time', 'status', 'created_at']
    
    def get_booking_type(self, obj):
        """Get booking type (user or team)."""
        return 'team' if obj.team else 'user'
