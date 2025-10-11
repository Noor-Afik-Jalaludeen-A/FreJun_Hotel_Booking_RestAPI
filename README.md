# FreJun Virtual Workspace Room Booking System

A comprehensive REST API for managing virtual workspace room bookings built with Django, Django REST Framework, SQLite, and Docker.

## 🏗️ Project Structure

```
frejun-booking/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── README.md
├── frejun_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── booking/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    └── tests.py
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (optional, for cloning)

### Setup and Run

1. **Clone or download the project**
   ```bash
   # If using git
   git clone <repository-url>
   cd frejun-booking
   
   # Or extract the project files to frejun-booking directory
   ```

2. **Build and run with Docker**
   ```bash
   docker compose up --build
   ```

3. **Access the API**
   - API Base URL: http://localhost:8000/api/v1/
   - Swagger Documentation: http://localhost:8000/swagger/
   - ReDoc Documentation: http://localhost:8000/redoc/
   - Django Admin: http://localhost:8000/admin/

### Manual Setup (Alternative)

If you prefer to run without Docker:

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the server**
   ```bash
   python manage.py runserver
   ```

## 📋 Business Rules

### Room Configuration
- **15 rooms total:**
  - 8 Private Rooms (1 user each)
  - 4 Conference Rooms (for teams with 3+ members)
  - 3 Shared Desks (each can hold up to 4 users)

### Booking Rules
- **Time Slots:** 9 AM to 6 PM (hourly slots only)
- **One booking per user/team:** Each user or team can book only one slot at a time
- **No overlapping bookings:** Same room cannot be double-booked
- **Shared desk capacity:** Fills sequentially (1-4 users)
- **Children handling:** Users under 10 are counted in headcount but don't occupy seats
- **Cancellation:** Frees up the slot for others
- **No availability:** Returns "No available room for the selected slot and type"

## 🔌 API Endpoints

### 1. Create Booking
**POST** `/api/v1/bookings/`

Create a new room booking.

**Request Body:**
```json
{
    "room_id": 1,
    "user_id": 1,  // For individual booking
    "team_id": 1,  // For team booking (use either user_id OR team_id)
    "date": "2024-01-15",
    "start_time": "10:00",
    "end_time": "11:00"
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "room": {
        "id": 1,
        "name": "Private Room 1",
        "room_type": "private",
        "capacity": 1
    },
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
    },
    "team": null,
    "date": "2024-01-15",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "status": "active",
    "created_at": "2024-01-15T10:00:00Z"
}
```

### 2. Cancel Booking
**POST** `/api/v1/cancel/{booking_id}/`

Cancel an existing booking.

**Response (200 OK):**
```json
{
    "id": 1,
    "room": {...},
    "user": {...},
    "date": "2024-01-15",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "status": "cancelled",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. List Bookings
**GET** `/api/v1/bookings/list/`

List all bookings with pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `status`: Filter by status (`active`, `cancelled`)

**Response (200 OK):**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/v1/bookings/list/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "room_name": "Private Room 1",
            "room_type": "private",
            "booking_type": "user",
            "user_name": "john_doe",
            "team_name": null,
            "date": "2024-01-15",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "status": "active",
            "created_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

### 4. Available Rooms
**GET** `/api/v1/rooms/available/?slot=10-11`

Get available rooms for a specific time slot.

**Query Parameters:**
- `slot`: Time slot in format `HH-HH` (required, e.g., `10-11`)
- `room_type`: Filter by room type (`private`, `conference`, `shared_desk`)
- `date`: Date in YYYY-MM-DD format (defaults to today)

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Private Room 1",
        "room_type": "private",
        "capacity": 1,
        "created_at": "2024-01-15T00:00:00Z"
    },
    {
        "id": 2,
        "name": "Private Room 2",
        "room_type": "private",
        "capacity": 1,
        "created_at": "2024-01-15T00:00:00Z"
    }
]
```

**No Available Rooms Response:**
```json
{
    "message": "No available room for the selected slot and type."
}
```

### 5. Additional Endpoints

- **GET** `/api/v1/rooms/` - List all rooms
- **GET** `/api/v1/teams/` - List all teams
- **GET** `/api/v1/users/` - List all users
- **GET** `/api/v1/health/` - Health check

## 🧪 Testing the API

### Using cURL

1. **Create a booking:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/bookings/ \
     -H "Content-Type: application/json" \
     -d '{
       "room_id": 1,
       "user_id": 1,
       "date": "2024-01-15",
       "start_time": "10:00",
       "end_time": "11:00"
     }'
   ```

2. **Check available rooms:**
   ```bash
   curl "http://localhost:8000/api/v1/rooms/available/?slot=10-11"
   ```

3. **List bookings:**
   ```bash
   curl "http://localhost:8000/api/v1/bookings/list/"
   ```

4. **Cancel a booking:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/cancel/1/
   ```

### Using Swagger UI

Visit http://localhost:8000/swagger/ to interact with the API through the web interface.

## 🗄️ Database Setup

The system uses SQLite by default. To set up the database:

1. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Create initial data (optional):**
   ```bash
   python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import User
   from booking.models import Room, Team, UserProfile
   
   # Create users
   user1 = User.objects.create_user('john', 'john@example.com', 'password')
   user2 = User.objects.create_user('jane', 'jane@example.com', 'password')
   
   # Create profiles
   UserProfile.objects.create(user=user1, age=25)
   UserProfile.objects.create(user=user2, age=30)
   
   # Create rooms
   for i in range(1, 9):
       Room.objects.create(name=f'Private Room {i}', room_type='private', capacity=1)
   
   for i in range(1, 5):
       Room.objects.create(name=f'Conference Room {i}', room_type='conference', capacity=5)
   
   for i in range(1, 4):
       Room.objects.create(name=f'Shared Desk {i}', room_type='shared_desk', capacity=4)
   
   # Create team
   team = Team.objects.create(name='Development Team')
   team.members.add(user1, user2)
   ```

## 🔧 Configuration

### Environment Variables
- `DEBUG`: Set to `1` for development mode
- `SECRET_KEY`: Django secret key (change in production)

### Django Settings
Key settings in `frejun_project/settings.py`:
- Database: SQLite (configurable)
- Pagination: 20 items per page
- API Documentation: Swagger/ReDoc enabled
- CORS: Configured for development

## 🚨 Error Handling

The API returns appropriate HTTP status codes and error messages:

- **400 Bad Request**: Validation errors, invalid parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server errors

Example error response:
```json
{
    "error": "User/Team already has a booking for this time slot"
}
```

## 🔒 Security Considerations

- **Race Conditions**: Handled using database transactions
- **Input Validation**: Comprehensive validation on all inputs
- **SQL Injection**: Protected by Django ORM
- **Authentication**: Ready for integration (currently open for testing)

## 📝 Assumptions Made

1. **Time Zone**: All times are in UTC
2. **Date Format**: ISO 8601 (YYYY-MM-DD)
3. **Time Format**: 24-hour format (HH:MM)
4. **Children Age**: Users under 10 are considered children
5. **Team Size**: Conference rooms require 3+ effective members
6. **Booking Duration**: All bookings are exactly 1 hour
7. **Operating Hours**: 9 AM to 6 PM only

## 🐛 Troubleshooting

### Common Issues

1. **Port 8000 already in use:**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Database migration errors:**
   ```bash
   # Reset database
   rm db.sqlite3
   python manage.py migrate
   ```

3. **Permission errors on Windows:**
   ```bash
   # Run PowerShell as Administrator
   ```

### Logs
Check Docker logs:
```bash
docker compose logs web
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For questions or issues:
- Check the API documentation at http://localhost:8000/swagger/
- Review the test cases in `booking/tests.py`
- Check Django logs for detailed error messages

---

**Happy Booking! 🎉**
