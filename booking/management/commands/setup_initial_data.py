"""
Management command to set up initial data for the booking system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from booking.models import Room, Team, UserProfile


class Command(BaseCommand):
    help = 'Set up initial data for the booking system'

    def handle(self, *args, **options):
        """Create initial users, rooms, and teams."""
        
        # Create users
        self.stdout.write('Creating users...')
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'age': 25},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'age': 30},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'age': 28},
            {'username': 'alice_brown', 'email': 'alice@example.com', 'age': 32},
            {'username': 'child_user', 'email': 'child@example.com', 'age': 8},
        ]
        
        created_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']}
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  Created user: {user.username}')
            else:
                self.stdout.write(f'  User already exists: {user.username}')
            
            # Create or update UserProfile for all users
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'age': user_data['age']}
            )
            if not profile_created:
                profile.age = user_data['age']
                profile.save()
                self.stdout.write(f'  Updated profile for: {user.username}')
            
            created_users.append(user)
        
        # Create rooms
        self.stdout.write('Creating rooms...')
        
        # Private rooms (8 total)
        for i in range(1, 9):
            room, created = Room.objects.get_or_create(
                name=f'Private Room {i}',
                defaults={
                    'room_type': 'private',
                    'capacity': 1
                }
            )
            if created:
                self.stdout.write(f'  Created room: {room.name}')
            else:
                self.stdout.write(f'  Room already exists: {room.name}')
        
        # Conference rooms (4 total)
        for i in range(1, 5):
            room, created = Room.objects.get_or_create(
                name=f'Conference Room {i}',
                defaults={
                    'room_type': 'conference',
                    'capacity': 5
                }
            )
            if created:
                self.stdout.write(f'  Created room: {room.name}')
            else:
                self.stdout.write(f'  Room already exists: {room.name}')
        
        # Shared desks (3 total)
        for i in range(1, 4):
            room, created = Room.objects.get_or_create(
                name=f'Shared Desk {i}',
                defaults={
                    'room_type': 'shared_desk',
                    'capacity': 4
                }
            )
            if created:
                self.stdout.write(f'  Created room: {room.name}')
            else:
                self.stdout.write(f'  Room already exists: {room.name}')
        
        # Create teams
        self.stdout.write('Creating teams...')
        
        # Development team
        dev_team, created = Team.objects.get_or_create(
            name='Development Team',
            defaults={}
        )
        if created:
            # Add adult users to the team
            adult_users = [user for user in created_users if user.profile.age >= 10]
            dev_team.members.set(adult_users)
            self.stdout.write(f'  Created team: {dev_team.name} with {dev_team.members.count()} members')
        else:
            self.stdout.write(f'  Team already exists: {dev_team.name}')
        
        # Marketing team
        marketing_team, created = Team.objects.get_or_create(
            name='Marketing Team',
            defaults={}
        )
        if created:
            # Add some users to marketing team
            marketing_users = created_users[:2]  # First 2 users
            marketing_team.members.set(marketing_users)
            self.stdout.write(f'  Created team: {marketing_team.name} with {marketing_team.members.count()} members')
        else:
            self.stdout.write(f'  Team already exists: {marketing_team.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Initial data setup completed successfully!\n'
                'You can now:\n'
                '1. Access the API at http://localhost:8000/api/v1/\n'
                '2. View documentation at http://localhost:8000/swagger/\n'
                '3. Access admin at http://localhost:8000/admin/\n'
                '4. Login with any created user (password: password123)'
            )
        )
