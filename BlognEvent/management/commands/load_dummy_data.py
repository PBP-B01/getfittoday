import os
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from BlognEvent.models import Event, Blogs
from home.models import FitnessSpot

class Command(BaseCommand):
    help = 'Loads dummy data from home/static/home/data/BlognEvent_data.json'

    def handle(self, *args, **options):
        # Clear existing data to avoid duplicates (optional, but recommended)
        self.stdout.write('Clearing old Blog and Event data...')
        Event.objects.all().delete()
        Blogs.objects.all().delete()
        
        # Build the path to the JSON file
        file_path = os.path.join(settings.BASE_DIR, 'home', 'static', 'home', 'data', 'BlognEvent_data.json')

        self.stdout.write(f'Loading data from {file_path}')

        try:
            with open(file_path) as f:
                data = json.load(f)

                # --- Load Blogs ---
                self.stdout.write('Loading blogs...')
                if 'blogs' not in data:
                    self.stdout.write(self.style.WARNING('No "blogs" key found in JSON file.'))
                else:
                    for blog_data in data['blogs']:
                        # Find or create the author
                        author, created = User.objects.get_or_create(
                            username=blog_data['author'],
                            defaults={'password': 'password123'} # Set a default password if new
                        )
                        if created:
                            self.stdout.write(f'Created user: {author.username}')

                        Blogs.objects.create(
                            id=blog_data['id'],
                            author=author,
                            title=blog_data['title'],
                            image=blog_data.get('image'), # Use .get() for safety
                            body=blog_data['body']
                        )
                    self.stdout.write(f'Successfully loaded {len(data["blogs"])} blogs.')

                # --- Load Events ---
                self.stdout.write('Loading events...')
                if 'events' not in data:
                     self.stdout.write(self.style.WARNING('No "events" key found in JSON file.'))
                else:
                    for event_data in data['events']:
                        # Find or create the user
                        user, created = User.objects.get_or_create(
                            username=event_data['user'],
                            defaults={'password': 'password123'}
                        )
                        if created:
                            self.stdout.write(f'Created user: {user.username}')

                        # Create the event object first
                        event = Event.objects.create(
                            id=event_data['id'],
                            user=user,
                            name=event_data['name'],
                            image=event_data.get('image'), # Use .get() for safety
                            description=event_data['description'],
                            starting_date=event_data['starting_date'],
                            ending_date=event_data['ending_date']
                        )

                        # Find/create and link locations
                        locations_to_add = []
                        for loc_name in event_data['locations']:
                            # Find or create the FitnessSpot
                            spot, created = FitnessSpot.objects.get_or_create(
                                name=loc_name,
                                defaults={
                                    'address': f'{loc_name} Dummy Address', # Add dummy defaults
                                    'latitude': 0.0,
                                    'longitude': 0.0,
                                    'place_id': f'dummy_{loc_name.replace(" ", "")}'
                                }
                            )
                            if created:
                                self.stdout.write(f'Created location: {spot.name}')
                            locations_to_add.append(spot)
                        
                        # Add all locations to the event
                        event.locations.set(locations_to_add)

                    self.stdout.write(f'Successfully loaded {len(data["events"])} events.')

                self.stdout.write(self.style.SUCCESS('Successfully loaded all dummy data.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: File not found at {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))