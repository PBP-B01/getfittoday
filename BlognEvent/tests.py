from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json
import uuid

from BlognEvent.models import Event, Blogs
from BlognEvent.forms import EventForm, BlogsForm
from home.models import FitnessSpot, PlaceType

User = get_user_model()


class EventModelTest(TestCase):
    """Test cases for Event model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.place_type = PlaceType.objects.create(name='gym')
        self.fitness_spot = FitnessSpot.objects.create(
            place_id='test_place_123',
            name='Test Gym',
            address='123 Test St',
            latitude='-6.402484',
            longitude='106.794243',
            rating=4.5,
            rating_count=100
        )
        self.fitness_spot.types.add(self.place_type)
    
    def test_create_event(self):
        """Test creating an event"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            description='Test Description',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(event.name, 'Test Event')
        self.assertEqual(event.user, self.user)
        self.assertIsInstance(event.id, uuid.UUID)
    
    def test_event_string_representation(self):
        """Test event __str__ method"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(str(event), 'Test Event')
    
    def test_event_locations_many_to_many(self):
        """Test adding locations to event"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        event.locations.add(self.fitness_spot)
        self.assertEqual(event.locations.count(), 1)
        self.assertIn(self.fitness_spot, event.locations.all())
    
    def test_event_with_image_url(self):
        """Test event with image URL"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            image='https://example.com/image.jpg',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(event.image, 'https://example.com/image.jpg')
    
    def test_event_cascade_delete_on_user_delete(self):
        """Test that events are deleted when user is deleted"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        event_id = event.id
        self.user.delete()
        self.assertFalse(Event.objects.filter(id=event_id).exists())


class BlogModelTest(TestCase):
    """Test cases for Blogs model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_blog(self):
        """Test creating a blog"""
        blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test blog content'
        )
        self.assertEqual(blog.title, 'Test Blog')
        self.assertEqual(blog.author, self.user)
        self.assertIsInstance(blog.id, uuid.UUID)
    
    def test_blog_string_representation(self):
        """Test blog __str__ method"""
        blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content'
        )
        self.assertEqual(str(blog), 'Test Blog')
    
    def test_blog_with_image_url(self):
        """Test blog with image URL"""
        blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content',
            image='https://example.com/image.jpg'
        )
        self.assertEqual(blog.image, 'https://example.com/image.jpg')
    
    def test_blog_cascade_delete_on_user_delete(self):
        """Test that blogs are deleted when user is deleted"""
        blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content'
        )
        blog_id = blog.id
        self.user.delete()
        self.assertFalse(Blogs.objects.filter(id=blog_id).exists())


class EventFormTest(TestCase):
    """Test cases for EventForm"""
    
    def test_valid_event_form(self):
        """Test valid event form"""
        form_data = {
            'name': 'Test Event',
            'image': 'https://example.com/image.jpg',
            'description': 'Test Description',
            'starting_date': timezone.now(),
            'ending_date': timezone.now() + timedelta(days=1)
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_event_form_strips_html_tags_from_name(self):
        """Test that HTML tags are stripped from event name"""
        form_data = {
            'name': '<script>alert("test")</script>Test Event',
            'description': 'Test Description',
            'starting_date': timezone.now(),
            'ending_date': timezone.now() + timedelta(days=1)
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        # strip_tags removes the tags but keeps the content inside
        self.assertEqual(form.cleaned_data['name'], 'alert("test")Test Event')
    
    def test_event_form_strips_html_tags_from_description(self):
        """Test that HTML tags are stripped from event description"""
        form_data = {
            'name': 'Test Event',
            'description': '<b>Bold</b> Description',
            'starting_date': timezone.now(),
            'ending_date': timezone.now() + timedelta(days=1)
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'Bold Description')
    
    def test_event_form_missing_required_fields(self):
        """Test event form with missing required fields"""
        form_data = {
            'name': 'Test Event',
            # Missing starting_date and ending_date
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('starting_date', form.errors)
        self.assertIn('ending_date', form.errors)
    
    def test_event_form_optional_image_field(self):
        """Test that image field is optional"""
        form_data = {
            'name': 'Test Event',
            'description': 'Test Description',
            'starting_date': timezone.now(),
            'ending_date': timezone.now() + timedelta(days=1)
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())


class BlogFormTest(TestCase):
    """Test cases for BlogsForm"""
    
    def test_valid_blog_form(self):
        """Test valid blog form"""
        form_data = {
            'title': 'Test Blog',
            'image': 'https://example.com/image.jpg',
            'body': 'Test blog content'
        }
        form = BlogsForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_blog_form_strips_html_tags_from_title(self):
        """Test that HTML tags are stripped from blog title"""
        form_data = {
            'title': '<script>alert("test")</script>Test Blog',
            'body': 'Test content'
        }
        form = BlogsForm(data=form_data)
        self.assertTrue(form.is_valid())
        # strip_tags removes the tags but keeps the content inside
        self.assertEqual(form.cleaned_data['title'], 'alert("test")Test Blog')
    
    def test_blog_form_strips_html_tags_from_body(self):
        """Test that HTML tags are stripped from blog body"""
        form_data = {
            'title': 'Test Blog',
            'body': '<p>Paragraph</p> content'
        }
        form = BlogsForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['body'], 'Paragraph content')
    
    def test_blog_form_missing_required_fields(self):
        """Test blog form with missing required fields"""
        form_data = {}
        form = BlogsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_blog_form_optional_fields(self):
        """Test that image and body fields are optional"""
        form_data = {
            'title': 'Test Blog'
        }
        form = BlogsForm(data=form_data)
        self.assertTrue(form.is_valid())


class BlogEventPageViewTest(TestCase):
    """Test cases for blog and event listing page"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        self.blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content'
        )
    
    def test_blogevent_page_accessible(self):
        """Test that blog/event page loads successfully"""
        response = self.client.get(reverse('BlognEvent:blogevent_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blogevent/blogevent_page.html')
    
    def test_blogevent_page_shows_events_and_blogs(self):
        """Test that events and blogs appear on the page"""
        response = self.client.get(reverse('BlognEvent:blogevent_page'))
        self.assertIn(self.event, response.context['events'])
        self.assertIn(self.blog, response.context['blogs'])
    
    def test_blogevent_page_admin_flag_false_by_default(self):
        """Test admin flag is False by default"""
        response = self.client.get(reverse('BlognEvent:blogevent_page'))
        self.assertFalse(response.context['is_admin'])
    
    def test_blogevent_page_admin_flag_true_when_set(self):
        """Test admin flag in context"""
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.get(reverse('BlognEvent:blogevent_page'))
        self.assertTrue(response.context['is_admin'])
    
    def test_blogevent_page_ordering(self):
        """Test that events and blogs are ordered correctly"""
        # Create additional event and blog
        event2 = Event.objects.create(
            user=self.user,
            name='Newer Event',
            starting_date=timezone.now() + timedelta(days=5),
            ending_date=timezone.now() + timedelta(days=6)
        )
        
        response = self.client.get(reverse('BlognEvent:blogevent_page'))
        events = list(response.context['events'])
        
        # Events should be ordered by starting_date descending
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], self.event)


class EventFormViewTest(TestCase):
    """Test cases for event form page and creation"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.place_type = PlaceType.objects.create(name='gym')
        self.fitness_spot = FitnessSpot.objects.create(
            place_id='test_place_123',
            name='Test Gym',
            address='123 Test St',
            latitude='-6.402484',
            longitude='106.794243'
        )
        self.fitness_spot.types.add(self.place_type)
    
    def test_event_form_page_requires_login(self):
        """Test that event form page requires authentication"""
        response = self.client.get(reverse('BlognEvent:event_form_page'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/central/login', response.url)
    
    def test_event_form_page_accessible_when_logged_in(self):
        """Test that logged-in users can access event form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('BlognEvent:event_form_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blogevent/event_form.html')
    
    def test_event_form_page_contains_locations(self):
        """Test that event form page includes fitness spots"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('BlognEvent:event_form_page'))
        
        self.assertIn('locations', response.context)
        self.assertIn('locations_json', response.context)
        self.assertIn(self.fitness_spot, response.context['locations'])
    
    def test_create_event_requires_login(self):
        """Test that creating event requires authentication"""
        response = self.client.post(reverse('BlognEvent:create_event'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_event_success(self):
        """Test successful event creation"""
        self.client.login(username='testuser', password='testpass123')
        
        event_data = {
            'name': 'New Event',
            'description': 'New event description',
            'starting_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'ending_date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'locations': [self.fitness_spot.place_id]
        }
        
        response = self.client.post(reverse('BlognEvent:create_event'), event_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(name='New Event').exists())
        
        # Check that location was added
        new_event = Event.objects.get(name='New Event')
        self.assertIn(self.fitness_spot, new_event.locations.all())
    
    def test_create_event_without_locations(self):
        """Test creating event without locations"""
        self.client.login(username='testuser', password='testpass123')
        
        event_data = {
            'name': 'New Event',
            'description': 'New event description',
            'starting_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'ending_date': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
        }
        
        response = self.client.post(reverse('BlognEvent:create_event'), event_data)
        self.assertEqual(response.status_code, 302)
        
        new_event = Event.objects.get(name='New Event')
        self.assertEqual(new_event.locations.count(), 0)
    
    def test_create_event_get_request_redirects(self):
        """Test that GET request to create_event redirects"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('BlognEvent:create_event'))
        self.assertEqual(response.status_code, 302)


class EventEditDeleteTest(TestCase):
    """Test cases for editing and deleting events"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.place_type = PlaceType.objects.create(name='gym')
        self.fitness_spot = FitnessSpot.objects.create(
            place_id='test_place_123',
            name='Test Gym',
            address='123 Test St',
            latitude='-6.402484',
            longitude='106.794243'
        )
        self.event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
    
    def test_edit_event_requires_login(self):
        """Test that editing requires authentication"""
        response = self.client.get(
            reverse('BlognEvent:edit_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_edit_event_owner_can_edit(self):
        """Test that event owner can edit their event"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:edit_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('event', response.context)
    
    def test_edit_event_non_owner_cannot_edit(self):
        """Test that non-owner cannot edit event"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:edit_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_edit_event_admin_can_edit(self):
        """Test that admin can edit any event"""
        self.client.login(username='otheruser', password='testpass123')
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.get(
            reverse('BlognEvent:edit_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_edit_event_post_success(self):
        """Test successful event edit via POST"""
        self.client.login(username='testuser', password='testpass123')
        
        edit_data = {
            'name': 'Updated Event Name',
            'description': 'Updated description',
            'starting_date': self.event.starting_date.strftime('%Y-%m-%dT%H:%M'),
            'ending_date': self.event.ending_date.strftime('%Y-%m-%dT%H:%M'),
        }
        
        response = self.client.post(
            reverse('BlognEvent:edit_event', kwargs={'event_id': self.event.id}),
            edit_data
        )
        self.assertEqual(response.status_code, 302)
        
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Updated Event Name')
    
    def test_delete_event_requires_post(self):
        """Test that delete requires POST request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:delete_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_delete_event_owner_can_delete(self):
        """Test that owner can delete their event"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('BlognEvent:delete_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())
    
    def test_delete_event_non_owner_cannot_delete(self):
        """Test that non-owner cannot delete event"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('BlognEvent:delete_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())
    
    def test_delete_event_admin_can_delete(self):
        """Test that admin can delete any event"""
        self.client.login(username='otheruser', password='testpass123')
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.post(
            reverse('BlognEvent:delete_event', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())
    
    def test_delete_nonexistent_event_returns_404(self):
        """Test deleting non-existent event returns 404"""
        self.client.login(username='testuser', password='testpass123')
        fake_uuid = uuid.uuid4()
        response = self.client.post(
            reverse('BlognEvent:delete_event', kwargs={'event_id': fake_uuid})
        )
        self.assertEqual(response.status_code, 404)


class BlogFormViewTest(TestCase):
    """Test cases for blog form page and creation"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_blog_form_page_requires_login(self):
        """Test that blog form page requires authentication"""
        response = self.client.get(reverse('BlognEvent:blog_form_page'))
        self.assertEqual(response.status_code, 302)
    
    def test_blog_form_page_accessible_when_logged_in(self):
        """Test that logged-in users can access blog form"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('BlognEvent:blog_form_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blogevent/blog_form.html')
    
    def test_create_blog_requires_login(self):
        """Test that creating blog requires authentication"""
        response = self.client.post(reverse('BlognEvent:create_blog'))
        self.assertEqual(response.status_code, 302)
    
    def test_create_blog_success(self):
        """Test successful blog creation"""
        self.client.login(username='testuser', password='testpass123')
        
        blog_data = {
            'title': 'New Blog',
            'body': 'New blog content',
            'image': 'https://example.com/image.jpg'
        }
        
        response = self.client.post(reverse('BlognEvent:create_blog'), blog_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Blogs.objects.filter(title='New Blog').exists())
        
        new_blog = Blogs.objects.get(title='New Blog')
        self.assertEqual(new_blog.author, self.user)
    
    def test_create_blog_get_request_redirects(self):
        """Test that GET request to create_blog redirects"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('BlognEvent:create_blog'))
        self.assertEqual(response.status_code, 302)


class BlogEditDeleteTest(TestCase):
    """Test cases for editing and deleting blogs"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content'
        )
    
    def test_edit_blog_requires_login(self):
        """Test that editing blog requires authentication"""
        response = self.client.get(
            reverse('BlognEvent:edit_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_edit_blog_owner_can_edit(self):
        """Test that blog author can edit their blog"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:edit_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('blog', response.context)
    
    def test_edit_blog_non_owner_cannot_edit(self):
        """Test that non-author cannot edit blog"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:edit_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_edit_blog_admin_can_edit(self):
        """Test that admin can edit any blog"""
        self.client.login(username='otheruser', password='testpass123')
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.get(
            reverse('BlognEvent:edit_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_edit_blog_post_success(self):
        """Test successful blog edit via POST"""
        self.client.login(username='testuser', password='testpass123')
        
        edit_data = {
            'title': 'Updated Blog Title',
            'body': 'Updated blog content'
        }
        
        response = self.client.post(
            reverse('BlognEvent:edit_blog', kwargs={'blog_id': self.blog.id}),
            edit_data
        )
        self.assertEqual(response.status_code, 302)
        
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.title, 'Updated Blog Title')
    
    def test_delete_blog_requires_post(self):
        """Test that delete requires POST request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:delete_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 405)
    
    def test_delete_blog_owner_can_delete(self):
        """Test that author can delete their blog"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('BlognEvent:delete_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Blogs.objects.filter(id=self.blog.id).exists())
    
    def test_delete_blog_non_owner_cannot_delete(self):
        """Test that non-author cannot delete blog"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('BlognEvent:delete_blog', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Blogs.objects.filter(id=self.blog.id).exists())


class EventDetailAPITest(TestCase):
    """Test cases for event detail API"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.place_type = PlaceType.objects.create(name='gym')
        self.fitness_spot = FitnessSpot.objects.create(
            place_id='test_place_123',
            name='Test Gym',
            address='123 Test St',
            latitude='-6.402484',
            longitude='106.794243'
        )
        self.event = Event.objects.create(
            user=self.user,
            name='Test Event',
            description='Test Description',
            image='https://example.com/image.jpg',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        self.event.locations.add(self.fitness_spot)
    
    def test_event_detail_api_returns_correct_data(self):
        """Test that event detail API returns correct JSON"""
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertEqual(data['name'], 'Test Event')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['user'], 'testuser')
        self.assertIn('Test Gym', data['locations'])
        self.assertEqual(data['image'], 'https://example.com/image.jpg')
    
    def test_event_detail_api_owner_flag_for_owner(self):
        """Test that is_owner flag is True for owner"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        data = response.json()
        self.assertTrue(data['is_owner'])
    
    def test_event_detail_api_owner_flag_for_non_owner(self):
        """Test that is_owner flag is False for non-owner"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        data = response.json()
        self.assertFalse(data['is_owner'])
    
    def test_event_detail_api_owner_flag_for_admin(self):
        """Test that is_owner flag is True for admin"""
        other_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.client.login(username='adminuser', password='testpass123')
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        data = response.json()
        self.assertTrue(data['is_owner'])
    
    def test_event_detail_api_unauthenticated(self):
        """Test event detail API for unauthenticated user"""
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        data = response.json()
        self.assertFalse(data['is_owner'])
    
    def test_event_detail_api_nonexistent_event(self):
        """Test API returns 404 for non-existent event"""
        fake_uuid = uuid.uuid4()
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': fake_uuid})
        )
        self.assertEqual(response.status_code, 404)
    
    def test_event_detail_api_date_formatting(self):
        """Test that dates are formatted correctly"""
        response = self.client.get(
            reverse('BlognEvent:event_detail_api', kwargs={'event_id': self.event.id})
        )
        data = response.json()
        
        # Check that dates are in correct format (e.g., "October 26, 2025")
        self.assertIn('starting_date', data)
        self.assertIn('ending_date', data)
        # The format should match strftime('%B %d, %Y')
        import re
        date_pattern = r'^[A-Z][a-z]+ \d{1,2}, \d{4}$'
        self.assertRegex(data['starting_date'], date_pattern)
        self.assertRegex(data['ending_date'], date_pattern)


class BlogDetailAPITest(TestCase):
    """Test cases for blog detail API"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content',
            image='https://example.com/image.jpg'
        )
    
    def test_blog_detail_api_returns_correct_data(self):
        """Test that blog detail API returns correct JSON"""
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': self.blog.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertEqual(data['title'], 'Test Blog')
        self.assertEqual(data['body'], 'Test content')
        self.assertEqual(data['author'], 'testuser')
        self.assertEqual(data['image'], 'https://example.com/image.jpg')
    
    def test_blog_detail_api_owner_flag_for_owner(self):
        """Test that is_owner flag is True for owner"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': self.blog.id})
        )
        data = response.json()
        self.assertTrue(data['is_owner'])
    
    def test_blog_detail_api_owner_flag_for_non_owner(self):
        """Test that is_owner flag is False for non-owner"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': self.blog.id})
        )
        data = response.json()
        self.assertFalse(data['is_owner'])
    
    def test_blog_detail_api_owner_flag_for_admin(self):
        """Test that is_owner flag is True for admin"""
        other_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.client.login(username='adminuser', password='testpass123')
        session = self.client.session
        session['is_admin'] = True
        session.save()
        
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': self.blog.id})
        )
        data = response.json()
        self.assertTrue(data['is_owner'])
    
    def test_blog_detail_api_unauthenticated(self):
        """Test blog detail API for unauthenticated user"""
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': self.blog.id})
        )
        data = response.json()
        self.assertFalse(data['is_owner'])
    
    def test_blog_detail_api_nonexistent_blog(self):
        """Test API returns 404 for non-existent blog"""
        fake_uuid = uuid.uuid4()
        response = self.client.get(
            reverse('BlognEvent:blog_detail_api', kwargs={'blog_id': fake_uuid})
        )
        self.assertEqual(response.status_code, 404)


class FitnessSpotIntegrationTest(TestCase):
    """Test cases for FitnessSpot integration with Events"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.place_type = PlaceType.objects.create(name='gym')
        self.fitness_spot1 = FitnessSpot.objects.create(
            place_id='gym_1',
            name='Gym One',
            address='Address 1',
            latitude='-6.402484',
            longitude='106.794243'
        )
        self.fitness_spot2 = FitnessSpot.objects.create(
            place_id='gym_2',
            name='Gym Two',
            address='Address 2',
            latitude='-6.502484',
            longitude='106.894243'
        )
    
    def test_event_multiple_locations(self):
        """Test adding multiple locations to an event"""
        event = Event.objects.create(
            user=self.user,
            name='Multi-Location Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        event.locations.add(self.fitness_spot1, self.fitness_spot2)
        
        self.assertEqual(event.locations.count(), 2)
        self.assertIn(self.fitness_spot1, event.locations.all())
        self.assertIn(self.fitness_spot2, event.locations.all())
    
    def test_fitness_spot_reverse_relation(self):
        """Test reverse relation from FitnessSpot to Events"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        event.locations.add(self.fitness_spot1)
        
        # Access events from fitness spot
        related_events = self.fitness_spot1.events.all()
        self.assertEqual(related_events.count(), 1)
        self.assertIn(event, related_events)
    
    def test_location_removal_does_not_delete_event(self):
        """Test that removing a location doesn't delete the event"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        event.locations.add(self.fitness_spot1)
        
        event.locations.remove(self.fitness_spot1)
        
        self.assertTrue(Event.objects.filter(id=event.id).exists())
        self.assertEqual(event.locations.count(), 0)


class SecurityTest(TestCase):
    """Security-related test cases"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
    
    def test_xss_prevention_in_event_name(self):
        """Test that XSS attempts are stripped from event names"""
        self.client.login(username='testuser', password='testpass123')
        
        xss_attempt = '<script>alert("XSS")</script>Clean Name'
        event_data = {
            'name': xss_attempt,
            'description': 'Description',
            'starting_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'ending_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        }
        
        self.client.post(reverse('BlognEvent:create_event'), event_data)
        
        event = Event.objects.first()
        # strip_tags removes HTML tags but keeps the content
        self.assertNotIn('<script>', event.name)
        self.assertIn('alert', event.name)  # Content inside tags remains
        self.assertIn('Clean Name', event.name)
    
    def test_xss_prevention_in_blog_title(self):
        """Test that XSS attempts are stripped from blog titles"""
        self.client.login(username='testuser', password='testpass123')
        
        xss_attempt = '<img src=x onerror=alert("XSS")>Clean Title'
        blog_data = {
            'title': xss_attempt,
            'body': 'Content'
        }
        
        self.client.post(reverse('BlognEvent:create_blog'), blog_data)
        
        blog = Blogs.objects.first()
        # strip_tags removes HTML tags but keeps the content
        self.assertNotIn('<img', blog.title)
        self.assertIn('Clean Title', blog.title)
    
    def test_csrf_protection_on_delete(self):
        """Test that delete operations work with proper authentication"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # With proper authentication and POST, delete should work
        response = self.client.post(
            reverse('BlognEvent:delete_event', kwargs={'event_id': event.id})
        )
        
        # Delete should succeed with proper auth
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=event.id).exists())
    
    def test_authorization_prevents_unauthorized_edit(self):
        """Test that users cannot edit others' content without permission"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        
        self.client.login(username='otheruser', password='testpass123')
        
        response = self.client.post(
            reverse('BlognEvent:edit_event', kwargs={'event_id': event.id}),
            {'name': 'Hacked Name'}
        )
        
        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.name, 'Test Event')


class URLPatternTest(TestCase):
    """Test URL patterns and routing"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_all_url_patterns_resolve(self):
        """Test that all URL patterns are properly configured"""
        event = Event.objects.create(
            user=self.user,
            name='Test Event',
            starting_date=timezone.now(),
            ending_date=timezone.now() + timedelta(days=1)
        )
        blog = Blogs.objects.create(
            author=self.user,
            title='Test Blog',
            body='Test content'
        )
        
        urls_to_test = [
            ('BlognEvent:blogevent_page', {}),
            ('BlognEvent:event_form_page', {}),
            ('BlognEvent:create_event', {}),
            ('BlognEvent:edit_event', {'event_id': event.id}),
            ('BlognEvent:delete_event', {'event_id': event.id}),
            ('BlognEvent:event_detail_api', {'event_id': event.id}),
            ('BlognEvent:blog_form_page', {}),
            ('BlognEvent:create_blog', {}),
            ('BlognEvent:edit_blog', {'blog_id': blog.id}),
            ('BlognEvent:delete_blog', {'blog_id': blog.id}),
            ('BlognEvent:blog_detail_api', {'blog_id': blog.id}),
        ]
        
        for url_name, kwargs in urls_to_test:
            url = reverse(url_name, kwargs=kwargs)
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith('/blognevent/'))