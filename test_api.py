#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints work correctly.
Run this after starting the server to test the API functionality.
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    """Test the main API endpoints."""
    print("🧪 Testing FreJun Room Booking API...")
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test get rooms
    print("\n2. Testing get rooms...")
    try:
        response = requests.get(f"{BASE_URL}/rooms/")
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Found {len(rooms)} rooms")
            if rooms:
                print(f"   First room: {rooms[0]['name']} ({rooms[0]['room_type']})")
        else:
            print(f"❌ Get rooms failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get rooms error: {e}")
    
    # Test get users
    print("\n3. Testing get users...")
    try:
        response = requests.get(f"{BASE_URL}/users/")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} users")
            if users:
                print(f"   First user: {users[0]['username']}")
        else:
            print(f"❌ Get users failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get users error: {e}")
    
    # Test get teams
    print("\n4. Testing get teams...")
    try:
        response = requests.get(f"{BASE_URL}/teams/")
        if response.status_code == 200:
            teams = response.json()
            print(f"✅ Found {len(teams)} teams")
            if teams:
                print(f"   First team: {teams[0]['name']} ({teams[0]['member_count']} members)")
        else:
            print(f"❌ Get teams failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get teams error: {e}")
    
    # Test available rooms
    print("\n5. Testing available rooms...")
    try:
        response = requests.get(f"{BASE_URL}/rooms/available/?slot=10-11")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ Found {len(data)} available rooms for 10-11 slot")
            else:
                print(f"✅ Response: {data.get('message', 'No message')}")
        else:
            print(f"❌ Available rooms failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Available rooms error: {e}")
    
    # Test create booking (if we have users and rooms)
    print("\n6. Testing create booking...")
    try:
        # Get first user and first private room
        users_response = requests.get(f"{BASE_URL}/users/")
        rooms_response = requests.get(f"{BASE_URL}/rooms/?room_type=private")
        
        if users_response.status_code == 200 and rooms_response.status_code == 200:
            users = users_response.json()
            rooms = rooms_response.json()
            
            if users and rooms:
                tomorrow = date.today() + timedelta(days=1)
                booking_data = {
                    "room_id": rooms[0]['id'],
                    "user_id": users[0]['id'],
                    "date": tomorrow.strftime("%Y-%m-%d"),
                    "start_time": "10:00",
                    "end_time": "11:00"
                }
                
                response = requests.post(
                    f"{BASE_URL}/bookings/",
                    json=booking_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 201:
                    booking = response.json()
                    print(f"✅ Created booking ID: {booking['id']}")
                    
                    # Test cancel booking
                    print("\n7. Testing cancel booking...")
                    cancel_response = requests.post(f"{BASE_URL}/cancel/{booking['id']}/")
                    if cancel_response.status_code == 200:
                        print("✅ Booking cancelled successfully")
                    else:
                        print(f"❌ Cancel booking failed: {cancel_response.status_code}")
                else:
                    print(f"❌ Create booking failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print("❌ No users or rooms available for booking test")
        else:
            print("❌ Could not fetch users or rooms for booking test")
    except Exception as e:
        print(f"❌ Create booking error: {e}")
    
    # Test list bookings
    print("\n8. Testing list bookings...")
    try:
        response = requests.get(f"{BASE_URL}/bookings/list/")
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                print(f"✅ Found {len(data['results'])} bookings")
            else:
                print(f"✅ Found {len(data)} bookings")
        else:
            print(f"❌ List bookings failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List bookings error: {e}")
    
    print("\n🎉 API testing completed!")
    print("\n📚 API Documentation available at:")
    print("   - Swagger UI: http://localhost:8000/swagger/")
    print("   - ReDoc: http://localhost:8000/redoc/")

if __name__ == "__main__":
    test_api()
