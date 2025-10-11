"""
Views for the Virtual Workspace Room Booking System.
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, time, date
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Room, Team, Booking, User, UserProfile
from .serializers import (
    BookingCreateSerializer, BookingSerializer, BookingListSerializer,
    AvailableRoomsSerializer, RoomSerializer, TeamSerializer, UserSerializer
)


class BookingCreateView(generics.CreateAPIView):
    """
    Create a new booking.
    
    POST /api/v1/bookings/
    """
    serializer_class = BookingCreateSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new room booking",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['room_id', 'date', 'start_time', 'end_time'],
            properties={
                'room_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Room ID'),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID (for individual booking)'),
                'team_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Team ID (for team booking)'),
                'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Booking date (YYYY-MM-DD)'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, description='Start time (HH:MM)'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, description='End time (HH:MM)'),
            }
        ),
        responses={
            201: BookingSerializer,
            400: 'Bad Request - Validation error',
            404: 'Not Found - Room/User/Team not found',
        }
    )
    def post(self, request, *args, **kwargs):
        """Create a new booking with race condition protection."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    booking = serializer.save()
                    response_serializer = BookingSerializer(booking)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingCancelView(APIView):
    """
    Cancel a booking.
    
    POST /api/v1/cancel/{booking_id}/
    """
    
    @swagger_auto_schema(
        operation_description="Cancel a booking by ID",
        responses={
            200: openapi.Response('Booking cancelled successfully', BookingSerializer),
            404: 'Not Found - Booking not found',
            400: 'Bad Request - Booking already cancelled',
        }
    )
    def post(self, request, booking_id):
        """Cancel a booking."""
        try:
            booking = get_object_or_404(Booking, id=booking_id)
            
            if booking.status == 'cancelled':
                return Response(
                    {'error': 'Booking is already cancelled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking.cancel()
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BookingListView(generics.ListAPIView):
    """
    List all bookings with pagination.
    
    GET /api/v1/bookings/
    """
    queryset = Booking.objects.all()
    serializer_class = BookingListSerializer
    
    @swagger_auto_schema(
        operation_description="List all bookings with pagination",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, cancelled)",
                type=openapi.TYPE_STRING,
                enum=['active', 'cancelled']
            ),
        ],
        responses={
            200: openapi.Response('List of bookings', BookingListSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        """List bookings with optional status filter."""
        queryset = self.get_queryset()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AvailableRoomsView(APIView):
    """
    List available rooms for a specific time slot.
    
    GET /api/v1/rooms/available/?slot=10-11
    """
    
    @swagger_auto_schema(
        operation_description="Get available rooms for a specific time slot",
        manual_parameters=[
            openapi.Parameter(
                'slot',
                openapi.IN_QUERY,
                description="Time slot in format 'HH-HH' (e.g., '10-11')",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'room_type',
                openapi.IN_QUERY,
                description="Filter by room type (private, conference, shared_desk)",
                type=openapi.TYPE_STRING,
                enum=['private', 'conference', 'shared_desk']
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Date for availability check (YYYY-MM-DD). Defaults to today.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
        ],
        responses={
            200: openapi.Response('List of available rooms', RoomSerializer(many=True)),
            400: 'Bad Request - Invalid slot format or parameters',
        }
    )
    def get(self, request):
        """Get available rooms for a specific time slot."""
        # Get query parameters
        slot = request.query_params.get('slot')
        room_type = request.query_params.get('room_type')
        date_str = request.query_params.get('date')
        
        if not slot:
            return Response(
                {'error': 'slot parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse slot
        try:
            start_hour, end_hour = slot.split('-')
            start_time = time(int(start_hour), 0)
            end_time = time(int(end_hour), 0)
        except (ValueError, IndexError):
            return Response(
                {'error': 'Invalid slot format. Use HH-HH (e.g., 10-11)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date (default to today)
        if date_str:
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            booking_date = date.today()
        
        # Validate time constraints
        if start_time < time(9, 0) or end_time > time(18, 0):
            return Response(
                {'error': 'Time slot must be between 9 AM and 6 PM'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if (end_time.hour - start_time.hour) != 1:
            return Response(
                {'error': 'Time slot must be exactly 1 hour'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get available rooms
        try:
            available_rooms = Booking.get_available_rooms(
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                room_type=room_type
            )
            
            if not available_rooms:
                return Response(
                    {'message': 'No available room for the selected slot and type.'},
                    status=status.HTTP_200_OK
                )
            
            serializer = RoomSerializer(available_rooms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoomListView(generics.ListAPIView):
    """
    List all rooms.
    
    GET /api/v1/rooms/
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    @swagger_auto_schema(
        operation_description="List all rooms",
        manual_parameters=[
            openapi.Parameter(
                'room_type',
                openapi.IN_QUERY,
                description="Filter by room type",
                type=openapi.TYPE_STRING,
                enum=['private', 'conference', 'shared_desk']
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """List rooms with optional type filter."""
        queryset = self.get_queryset()
        
        # Filter by room type if provided
        room_type = request.query_params.get('room_type')
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TeamListView(generics.ListCreateAPIView):
    """
    List all teams or create a new team.
    
    GET /api/v1/teams/
    POST /api/v1/teams/
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class UserListView(generics.ListAPIView):
    """
    List all users.
    
    GET /api/v1/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.
    
    GET /api/v1/health/
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'FreJun Room Booking API'
    })
