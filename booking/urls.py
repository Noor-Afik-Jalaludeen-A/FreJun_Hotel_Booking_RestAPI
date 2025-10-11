"""
URL configuration for the booking app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main API endpoints
    path('bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('bookings/list/', views.BookingListView.as_view(), name='booking-list'),
    path('cancel/<int:booking_id>/', views.BookingCancelView.as_view(), name='booking-cancel'),
    path('rooms/available/', views.AvailableRoomsView.as_view(), name='rooms-available'),
    
    # Additional endpoints
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('teams/', views.TeamListView.as_view(), name='team-list'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('health/', views.health_check, name='health-check'),
]
