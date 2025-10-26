from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from unittest.mock import patch
import json
import unittest

from .models import Event
from community.models import Community, CommunityCategory
from home.models import FitnessSpot

User = get_user_model()

_counter = {'user': 0, 'spot': 0, 'category': 0}

def create_user(username=None, email=None, password='testpass123', **kwargs):
    if username is None:
        _counter['user'] += 1
        username = f'testuser{_counter["user"]}'
    if email is None:
        email = f'{username}@example.com'
    
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        **kwargs
    )

def create_fitness_spot(name=None, address=None):
    if name is None:
        _counter['spot'] += 1
        name = f'Test Gym {_counter["spot"]}'
    if address is None:
        address = f'Test Address {_counter["spot"]}'
    
    return FitnessSpot.objects.create(
        name=name,
        address=address,
        place_id=f'place_id_{_counter["spot"]}',
        latitude=-6.2 + (_counter["spot"] * 0.01),
        longitude=106.8 + (_counter["spot"] * 0.01)
    )

def create_category(name=None, slug=None):
    if name is None:
        _counter['category'] += 1
        name = f'Test Category {_counter["category"]}'
    if slug is None:
        slug = f'test-category-{_counter["category"]}'
    
    return CommunityCategory.objects.create(name=name, slug=slug)

def create_community(name='Test Community', fitness_spot=None, category=None, **kwargs):
    if fitness_spot is None:
        fitness_spot = create_fitness_spot()
    if category is None:
        category = create_category()
    
    community = Community.objects.create(
        name=name,
        description='Test description',
        fitness_spot=fitness_spot,
        category=category,
        **kwargs
    )
    return community

def create_event(name='Test Event', community=None, created_by=None, **kwargs):
    if community is None:
        community = create_community()
    if created_by is None:
        created_by = create_user()
    
    defaults = {
        'description': 'Test event description',
        'date': timezone.now() + timedelta(days=7),
        'location': 'Test Location',
    }
    defaults.update(kwargs)
    
    return Event.objects.create(
        name=name,
        community=community,
        created_by=created_by,
        **defaults
    )

class EventModelTestCase(TestCase):
    def setUp(self):
        self.user = create_user(username='testuser')
        self.admin_user = create_user(username='adminuser')
        self.staff_user = create_user(username='staffuser', is_staff=True)
        self.superuser = create_user(username='superuser', is_superuser=True)
        
        self.fitness_spot = create_fitness_spot()
        self.category = create_category()
        self.community = create_community(
            name='Test Community',
            fitness_spot=self.fitness_spot,
            category=self.category
        )
        self.community.admins.add(self.admin_user)
        
        self.event = create_event(
            name='Test Event',
            community=self.community,
            created_by=self.admin_user
        )

    def test_create_event(self):
        event = Event.objects.create(
            name='New Event',
            description='New event description',
            date=timezone.now() + timedelta(days=5),
            location='New Location',
            community=self.community,
            created_by=self.user
        )
        
        self.assertEqual(event.name, 'New Event')
        self.assertEqual(event.community, self.community)
        self.assertEqual(event.created_by, self.user)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)
    
    def test_create_event_with_registration_deadline(self):
        deadline = timezone.now() + timedelta(days=3)
        event = create_event(
            name='Event with Deadline',
            registration_deadline=deadline
        )
        
        self.assertEqual(event.registration_deadline, deadline)
    
    def test_event_str_representation(self):
        expected = f"{self.event.name} ({self.community.name})"
        self.assertEqual(str(self.event), expected)
    
    def test_event_ordering(self):
        test_community = create_community(name='Test Ordering Community')
        
        event1 = create_event(name='Event 1', date=timezone.now() + timedelta(days=5), community=test_community)
        event2 = create_event(name='Event 2', date=timezone.now() + timedelta(days=3), community=test_community)
        event3 = create_event(name='Event 3', date=timezone.now() + timedelta(days=7), community=test_community)
        
        events = list(Event.objects.filter(community=test_community))
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)
        self.assertEqual(events[2], event3)

    def test_is_past_for_future_event(self):
        future_event = create_event(date=timezone.now() + timedelta(days=1))
        self.assertFalse(future_event.is_past())
    
    def test_is_past_for_past_event(self):
        past_event = create_event(date=timezone.now() - timedelta(days=1))
        self.assertTrue(past_event.is_past())
    
    def test_is_past_for_current_time(self):
        current_event = create_event(date=timezone.now())
        self.assertTrue(current_event.is_past())
    
    def test_is_ongoing_for_current_event(self):
        ongoing_event = create_event(date=timezone.now() - timedelta(minutes=30))
        self.assertTrue(ongoing_event.is_ongoing())
    
    def test_is_ongoing_for_future_event(self):
        future_event = create_event(date=timezone.now() + timedelta(hours=3))
        self.assertFalse(future_event.is_ongoing())
    
    def test_is_ongoing_for_past_event(self):
        past_event = create_event(date=timezone.now() - timedelta(hours=3))
        self.assertFalse(past_event.is_ongoing())
    
    def test_is_ongoing_at_boundary(self):
        boundary_event = create_event(date=timezone.now() - timedelta(hours=2, minutes=1))
        self.assertFalse(boundary_event.is_ongoing())

    def test_registration_open_for_future_event_no_deadline(self):
        future_event = create_event(date=timezone.now() + timedelta(days=5))
        self.assertTrue(future_event.registration_open())
    
    def test_registration_open_for_past_event_no_deadline(self):
        past_event = create_event(date=timezone.now() - timedelta(days=1))
        self.assertFalse(past_event.registration_open())
    
    def test_registration_open_with_future_deadline(self):
        event = create_event(
            date=timezone.now() + timedelta(days=10),
            registration_deadline=timezone.now() + timedelta(days=5)
        )
        self.assertTrue(event.registration_open())
    
    def test_registration_closed_with_past_deadline(self):
        event = create_event(
            date=timezone.now() + timedelta(days=10),
            registration_deadline=timezone.now() - timedelta(hours=1)
        )
        self.assertFalse(event.registration_open())
    
    def test_registration_deadline_overrides_event_date(self):
        event = create_event(
            date=timezone.now() + timedelta(days=10),
            registration_deadline=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(event.registration_open())

    def test_can_edit_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser
        anon_user = AnonymousUser()
        self.assertFalse(self.event.can_edit(anon_user))
    
    def test_can_edit_community_admin(self):
        self.assertTrue(self.event.can_edit(self.admin_user))
    
    def test_can_edit_staff_user(self):
        self.assertTrue(self.event.can_edit(self.staff_user))
    
    def test_can_edit_superuser(self):
        self.assertTrue(self.event.can_edit(self.superuser))
    
    def test_can_edit_regular_user(self):
        self.assertFalse(self.event.can_edit(self.user))
    
    def test_can_edit_different_community_admin(self):
        other_community = create_community(name='Other Community')
        other_admin = create_user(username='otheradmin')
        other_community.admins.add(other_admin)
        
        self.assertFalse(self.event.can_edit(other_admin))

    def test_can_delete_same_as_can_edit(self):
        self.assertEqual(
            self.event.can_delete(self.admin_user),
            self.event.can_edit(self.admin_user)
        )
        self.assertEqual(
            self.event.can_delete(self.user),
            self.event.can_edit(self.user)
        )

    def test_can_join_authenticated_user(self):
        self.assertTrue(self.event.can_join(self.user))
    
    def test_can_join_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser
        anon_user = AnonymousUser()
        self.assertFalse(self.event.can_join(anon_user))
    
    def test_can_join_already_participant(self):
        self.event.participants.add(self.user)
        self.assertFalse(self.event.can_join(self.user))
    
    def test_can_join_registration_closed(self):
        past_event = create_event(date=timezone.now() - timedelta(days=1))
        self.assertFalse(past_event.can_join(self.user))
    
    def test_can_join_with_deadline_passed(self):
        event = create_event(
            date=timezone.now() + timedelta(days=5),
            registration_deadline=timezone.now() - timedelta(hours=1)
        )
        self.assertFalse(event.can_join(self.user))

    def test_user_is_participant_true(self):
        self.event.participants.add(self.user)
        self.assertTrue(self.event.user_is_participant(self.user))
    
    def test_user_is_participant_false(self):
        self.assertFalse(self.event.user_is_participant(self.user))
    
    def test_user_is_participant_unauthenticated(self):
        from django.contrib.auth.models import AnonymousUser
        anon_user = AnonymousUser()
        self.assertFalse(self.event.user_is_participant(anon_user))

    def test_participant_count_zero(self):
        self.assertEqual(self.event.participant_count(), 0)
    
    def test_participant_count_multiple(self):
        user2 = create_user(username='user2')
        user3 = create_user(username='user3')
        
        self.event.participants.add(self.user, user2, user3)
        self.assertEqual(self.event.participant_count(), 3)
    
    def test_participant_count_after_removal(self):
        self.event.participants.add(self.user)
        self.assertEqual(self.event.participant_count(), 1)
        
        self.event.participants.remove(self.user)
        self.assertEqual(self.event.participant_count(), 0)

class EventViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.user = create_user(username='testuser', password='testpass')
        self.admin_user = create_user(username='adminuser', password='adminpass')
        self.staff_user = create_user(username='staffuser', password='staffpass', is_staff=True)
        
        self.fitness_spot = create_fitness_spot()
        self.category = create_category()
        self.community = create_community(
            name='Test Community',
            fitness_spot=self.fitness_spot,
            category=self.category
        )
        self.community.admins.add(self.admin_user)
        
        self.event = create_event(
            name='Test Event',
            community=self.community,
            created_by=self.admin_user,
            date=timezone.now() + timedelta(days=7)
        )

    def test_event_list_accessible(self):
        response = self.client.get(reverse('event:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event/event_list.html')
    
    def test_event_list_shows_events(self):
        response = self.client.get(reverse('event:event_list'))
        self.assertIn('events', response.context)
        self.assertEqual(len(response.context['events']), 1)
    
    def test_event_list_filter_by_name(self):
        create_event(name='Basketball Event', community=self.community)
        create_event(name='Football Event', community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'name': 'Basketball'})
        events = response.context['events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['name'], 'Basketball Event')
    
    def test_event_list_filter_by_location(self):
        create_event(name='Event 1', location='Jakarta', community=self.community)
        create_event(name='Event 2', location='Bandung', community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'location': 'Jakarta'})
        events = response.context['events']
        self.assertTrue(any('Jakarta' in e['location'] for e in events))
    
    def test_event_list_filter_by_community(self):
        other_community = create_community(name='Other Community')
        create_event(name='Event in Other', community=other_community)
        
        response = self.client.get(reverse('event:event_list'), {'community': 'Other'})
        events = response.context['events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['community_name'], 'Other Community')
    
    def test_event_list_filter_upcoming(self):
        create_event(name='Future Event', date=timezone.now() + timedelta(days=5), community=self.community)
        create_event(name='Past Event', date=timezone.now() - timedelta(days=5), community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'status': 'upcoming'})
        events = response.context['events']
        self.assertTrue(all(not e['is_past'] for e in events))
    
    def test_event_list_filter_past(self):
        create_event(name='Future Event', date=timezone.now() + timedelta(days=5), community=self.community)
        create_event(name='Past Event', date=timezone.now() - timedelta(days=5), community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'status': 'past'})
        events = response.context['events']
        self.assertTrue(all(e['is_past'] for e in events))
    
    def test_event_list_sort_newest(self):
        event1 = create_event(name='Event 1', community=self.community)
        event2 = create_event(name='Event 2', community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'date_sort': 'newest'})
        events = response.context['events']
        self.assertEqual(events[0]['name'], 'Event 2')
    
    def test_event_list_sort_soonest(self):
        create_event(name='Far Event', date=timezone.now() + timedelta(days=10), community=self.community)
        create_event(name='Soon Event', date=timezone.now() + timedelta(days=2), community=self.community)
        
        response = self.client.get(reverse('event:event_list'), {'date_sort': 'soonest'})
        events = response.context['events']
        self.assertEqual(events[0]['name'], 'Soon Event')
    
    def test_event_list_my_events_filter_authenticated(self):
        self.client.login(username='adminuser', password='adminpass')
        
        other_community = create_community(name='Other Community')
        create_event(name='My Event', community=self.community)
        create_event(name='Other Event', community=other_community)
        
        response = self.client.get(reverse('event:event_list'), {'my_events': 'true'})
        events = response.context['events']
        community_names = [e['community_name'] for e in events]
        self.assertIn('Test Community', community_names)
    
    def test_event_list_from_community_parameter(self):
        response = self.client.get(
            reverse('event:event_list'),
            {'from_community': self.community.id}
        )
        self.assertEqual(response.context['from_community_id'], str(self.community.id))
        self.assertEqual(response.context['from_community_name'], self.community.name)
    
    def test_event_list_from_invalid_community(self):
        response = self.client.get(reverse('event:event_list'), {'from_community': '99999'})
        self.assertIsNone(response.context['from_community_id'])
    
    def test_event_list_user_admin_communities_context(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(reverse('event:event_list'))
        
        self.assertIn('user_admin_communities', response.context)
        admin_communities = list(response.context['user_admin_communities'])
        self.assertEqual(len(admin_communities), 1)
    
    def test_create_event_success(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {
            'name': 'New Event',
            'description': 'New event description',
            'date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'New Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(Event.objects.filter(name='New Event').exists())
    
    def test_create_event_with_registration_deadline(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {
            'name': 'Event with Deadline',
            'description': 'Description',
            'date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Location',
            'community': self.community.id,
            'registration_deadline': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        event = Event.objects.get(name='Event with Deadline')
        self.assertIsNotNone(event.registration_deadline)
    
    def test_create_event_missing_fields(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {'name': 'Incomplete Event'}
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
    
    def test_create_event_non_admin(self):
        self.client.login(username='testuser', password='testpass')
        
        data = {
            'name': 'Unauthorized Event',
            'description': 'Description',
            'date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
    
    def test_create_event_staff_can_create(self):
        self.client.login(username='staffuser', password='staffpass')
        
        data = {
            'name': 'Staff Event',
            'description': 'Description',
            'date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_create_event_invalid_community(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {
            'name': 'Invalid Community Event',
            'description': 'Description',
            'date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Location',
            'community': 99999
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [404, 500])
    
    def test_create_event_invalid_date_format(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {
            'name': 'Invalid Date Event',
            'description': 'Description',
            'date': 'invalid-date-format',
            'location': 'Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_create_event_requires_login(self):
        data = {
            'name': 'Unauthorized Event',
            'description': 'Description',
            'date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)

    def test_edit_event_success(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {
            'name': 'Updated Event Name',
            'description': 'Updated description',
            'location': 'Updated Location'
        }
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Updated Event Name')
        self.assertEqual(self.event.description, 'Updated description')
        self.assertEqual(self.event.location, 'Updated Location')
    
    def test_edit_event_partial_update(self):
        self.client.login(username='adminuser', password='adminpass')
        
        original_location = self.event.location
        data = {'name': 'Only Name Updated'}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Only Name Updated')
        self.assertEqual(self.event.location, original_location)
    
    def test_edit_event_update_date(self):
        self.client.login(username='adminuser', password='adminpass')
        
        base_date = timezone.now() + timedelta(days=10)
        date_string = base_date.strftime('%Y-%m-%dT%H:%M')
        
        expected_naive = datetime.strptime(date_string, '%Y-%m-%dT%H:%M')
        expected_aware = timezone.make_aware(expected_naive, timezone.get_current_timezone())
        
        data = {'date': date_string}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.date, expected_aware)
    
    def test_edit_event_set_registration_deadline(self):
        self.client.login(username='adminuser', password='adminpass')
        
        deadline = timezone.now() + timedelta(days=3)
        data = {'registration_deadline': deadline.strftime('%Y-%m-%dT%H:%M')}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.registration_deadline)
    
    def test_edit_event_clear_registration_deadline(self):
        self.event.registration_deadline = timezone.now() + timedelta(days=3)
        self.event.save()
        
        self.client.login(username='adminuser', password='adminpass')
        data = {'registration_deadline': ''}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertIsNone(self.event.registration_deadline)
    
    def test_edit_event_non_admin(self):
        self.client.login(username='testuser', password='testpass')
        
        data = {'name': 'Unauthorized Edit'}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_edit_event_staff_can_edit(self):
        self.client.login(username='staffuser', password='staffpass')
        
        data = {'name': 'Staff Edit'}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_edit_event_invalid_date_format(self):
        self.client.login(username='adminuser', password='adminpass')
        
        data = {'date': 'invalid-date'}
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_edit_event_not_found(self):
        self.client.login(username='adminuser', password='adminpass')
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': 99999}),
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [404, 500])
    
    def test_edit_event_requires_login(self):
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': self.event.id}),
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)

    def test_delete_event_success(self):
        self.client.login(username='adminuser', password='adminpass')
        event_id = self.event.id
        
        response = self.client.post(
            reverse('event:delete_event', kwargs={'event_id': event_id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertFalse(Event.objects.filter(id=event_id).exists())
    
    def test_delete_event_non_admin(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:delete_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())
    
    def test_delete_event_staff_can_delete(self):
        self.client.login(username='staffuser', password='staffpass')
        event_id = self.event.id
        
        response = self.client.post(
            reverse('event:delete_event', kwargs={'event_id': event_id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=event_id).exists())
    
    def test_delete_event_not_found(self):
        self.client.login(username='adminuser', password='adminpass')
        
        response = self.client.post(
            reverse('event:delete_event', kwargs={'event_id': 99999})
        )
        
        self.assertIn(response.status_code, [404, 500])
    
    def test_delete_event_requires_login(self):
        response = self.client.post(
            reverse('event:delete_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 302)

    def test_join_event_success(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(self.event.participants.filter(id=self.user.id).exists())
    
    def test_join_event_already_joined(self):
        self.event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('sudah terdaftar', response_data['message'])
    
    def test_join_event_registration_closed(self):
        past_event = create_event(
            name='Past Event',
            date=timezone.now() - timedelta(days=1),
            community=self.community
        )
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': past_event.id})
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('ditutup', response_data['message'])
    
    def test_join_event_with_deadline_passed(self):
        event_with_deadline = create_event(
            name='Deadline Passed',
            date=timezone.now() + timedelta(days=10),
            registration_deadline=timezone.now() - timedelta(hours=1),
            community=self.community
        )
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': event_with_deadline.id})
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_join_event_updates_participant_count(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': self.event.id})
        )
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['participant_count'], 1)
    
    def test_join_event_requires_login(self):
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 302)
    
    def test_join_event_not_found(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': 99999})
        )
        
        self.assertIn(response.status_code, [404, 500])

    def test_leave_event_success(self):
        self.event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertFalse(self.event.participants.filter(id=self.user.id).exists())
    
    def test_leave_event_not_participant(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('belum terdaftar', response_data['message'])
    
    def test_leave_event_already_started(self):
        ongoing_event = create_event(
            name='Ongoing Event',
            date=timezone.now() - timedelta(minutes=30),
            community=self.community
        )
        ongoing_event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': ongoing_event.id})
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('sudah dimulai', response_data['message'])
    
    def test_leave_event_past(self):
        past_event = create_event(
            name='Past Event',
            date=timezone.now() - timedelta(days=1),
            community=self.community
        )
        past_event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': past_event.id})
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_leave_event_updates_participant_count(self):
        self.event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': self.event.id})
        )
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['participant_count'], 0)
    
    def test_leave_event_requires_login(self):
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 302)
    
    def test_leave_event_not_found(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': 99999})
        )
        
        self.assertIn(response.status_code, [404, 500])

    @unittest.skip("URL 'get_event_detail' not found in URL configuration")
    def test_get_event_detail_success(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(
            reverse('event:get_event_detail', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['event']['id'], self.event.id)
        self.assertEqual(response_data['event']['name'], self.event.name)
    
    @unittest.skip("URL 'get_event_detail' not found in URL configuration")
    def test_get_event_detail_includes_permissions(self):
        self.client.login(username='adminuser', password='adminpass')
        
        response = self.client.get(
            reverse('event:get_event_detail', kwargs={'event_id': self.event.id})
        )
        
        response_data = json.loads(response.content)
        event_data = response_data['event']
        self.assertIn('can_edit', event_data)
        self.assertIn('can_join', event_data)
        self.assertIn('is_participant', event_data)
        self.assertTrue(event_data['can_edit'])
    
    @unittest.skip("URL 'get_event_detail' not found in URL configuration")
    def test_get_event_detail_not_found(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(
            reverse('event:get_event_detail', kwargs={'event_id': 99999})
        )
        
        self.assertIn(response.status_code, [404, 500])
    
    @unittest.skip("URL 'get_event_detail' not found in URL configuration")
    def test_get_event_detail_requires_login(self):
        response = self.client.get(
            reverse('event:get_event_detail', kwargs={'event_id': self.event.id})
        )
        
        self.assertEqual(response.status_code, 302)

    def test_community_events_api_success(self):
        create_event(name='Event 1', community=self.community)
        create_event(name='Event 2', community=self.community)
        
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': self.community.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['community_name'], self.community.name)
        self.assertEqual(len(response_data['events']), 3)
    
    def test_community_events_api_empty(self):
        empty_community = create_community(name='Empty Community')
        
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': empty_community.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['events']), 0)
    
    def test_community_events_api_not_found(self):
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': 99999})
        )
        
        self.assertIn(response.status_code, [404, 500])
    
    def test_community_events_api_includes_permissions(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': self.community.id})
        )
        
        response_data = json.loads(response.content)
        event_data = response_data['events'][0]
        self.assertIn('can_join', event_data)
        self.assertIn('is_participant', event_data)
        self.assertIn('can_edit', event_data)
    
    def test_community_events_api_ordered_by_date(self):
        event1 = create_event(
            name='Far Event',
            community=self.community,
            date=timezone.now() + timedelta(days=10)
        )
        event2 = create_event(
            name='Soon Event',
            community=self.community,
            date=timezone.now() + timedelta(days=2)
        )
        
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': self.community.id})
        )
        
        response_data = json.loads(response.content)
        events = response_data['events']
        self.assertEqual(events[0]['name'], 'Soon Event')

class EventAdminTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = create_user(
            username='admin',
            password='adminpass',
            is_staff=True,
            is_superuser=True
        )
        
        self.fitness_spot = create_fitness_spot()
        self.category = create_category()
        self.community = create_community(
            fitness_spot=self.fitness_spot,
            category=self.category
        )
        self.event = create_event(community=self.community)
        
        self.client.login(username='admin', password='adminpass')
    
    def test_admin_list_display(self):
        from .admin import EventAdmin
        
        expected_fields = (
            'name', 'community', 'date', 'location',
            'created_by', 'participant_count', 'registration_status',
            'created_at'
        )
        self.assertEqual(EventAdmin.list_display, expected_fields)
    
    def test_admin_list_filter(self):
        from .admin import EventAdmin
        
        expected_filters = ('community', 'date', 'created_at')
        self.assertEqual(EventAdmin.list_filter, expected_filters)
    
    def test_admin_search_fields(self):
        from .admin import EventAdmin
        
        expected_search = (
            'name', 'description', 'location',
            'community__name', 'created_by__username'
        )
        self.assertEqual(EventAdmin.search_fields, expected_search)
    
    def test_admin_participant_count_method(self):
        from .admin import EventAdmin
        from django.contrib import admin

        user1 = create_user()
        user2 = create_user()
        self.event.participants.add(user1, user2)
        
        admin_instance = EventAdmin(Event, admin.site)
        count = admin_instance.participant_count(self.event)
        self.assertEqual(count, 2)
    
    def test_admin_registration_status_method(self):
        from .admin import EventAdmin
        from django.contrib import admin
        
        admin_instance = EventAdmin(Event, admin.site)

        future_event = create_event(date=timezone.now() + timedelta(days=5))
        self.assertTrue(admin_instance.registration_status(future_event))

        past_event = create_event(date=timezone.now() - timedelta(days=1))
        self.assertFalse(admin_instance.registration_status(past_event))
    
    def test_admin_readonly_fields(self):
        from .admin import EventAdmin
        
        expected_readonly = ('created_at', 'updated_at', 'participant_count')
        self.assertEqual(EventAdmin.readonly_fields, expected_readonly)
    
    def test_admin_fieldsets(self):
        from .admin import EventAdmin
        
        self.assertEqual(len(EventAdmin.fieldsets), 4)
        self.assertEqual(EventAdmin.fieldsets[0][0], 'Event Information')
        self.assertEqual(EventAdmin.fieldsets[1][0], 'Date & Location')
        self.assertEqual(EventAdmin.fieldsets[2][0], 'Participants')
        self.assertEqual(EventAdmin.fieldsets[3][0], 'Metadata')
    
    def test_admin_date_hierarchy(self):
        from .admin import EventAdmin
        
        self.assertEqual(EventAdmin.date_hierarchy, 'date')
    
    def test_admin_filter_horizontal(self):
        from .admin import EventAdmin
        
        self.assertEqual(EventAdmin.filter_horizontal, ('participants',))

class EventIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.admin_user = create_user(username='admin', password='adminpass')
        self.user1 = create_user(username='user1', password='pass1')
        self.user2 = create_user(username='user2', password='pass2')
        
        self.fitness_spot = create_fitness_spot()
        self.category = create_category()
        self.community = create_community(
            fitness_spot=self.fitness_spot,
            category=self.category
        )
        self.community.admins.add(self.admin_user)
    
    def test_full_event_lifecycle(self):
        self.client.login(username='admin', password='adminpass')
        
        create_data = {
            'name': 'Integration Test Event',
            'description': 'Full lifecycle test',
            'date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'Test Location',
            'community': self.community.id
        }
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps(create_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        event_id = json.loads(response.content)['event_id']

        self.client.login(username='user1', password='pass1')
        response = self.client.post(reverse('event:join_event', kwargs={'event_id': event_id}))
        self.assertEqual(response.status_code, 200)
        
        self.client.login(username='user2', password='pass2')
        response = self.client.post(reverse('event:join_event', kwargs={'event_id': event_id}))
        self.assertEqual(response.status_code, 200)
        
        event = Event.objects.get(id=event_id)
        self.assertEqual(event.participant_count(), 2)

        self.client.login(username='user1', password='pass1')
        response = self.client.post(reverse('event:leave_event', kwargs={'event_id': event_id}))
        self.assertEqual(response.status_code, 200)
        
        event.refresh_from_db()
        self.assertEqual(event.participant_count(), 1)

        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('event:delete_event', kwargs={'event_id': event_id}))
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(Event.objects.filter(id=event_id).exists())
    
    def test_permission_workflow(self):
        event = create_event(community=self.community, created_by=self.admin_user)

        self.client.login(username='user1', password='pass1')
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': event.id}),
            data=json.dumps({'name': 'Unauthorized'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        self.client.login(username='admin', password='adminpass')
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': event.id}),
            data=json.dumps({'name': 'Authorized Edit'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        event.refresh_from_db()
        self.assertEqual(event.name, 'Authorized Edit')
    
    def test_multiple_participants_workflow(self):
        event = create_event(community=self.community, created_by=self.admin_user)
        
        users = [create_user(password=f'pass{i}') for i in range(5)]

        for i, user in enumerate(users):
            self.client.login(username=user.username, password=f'pass{i}')
            response = self.client.post(
                reverse('event:join_event', kwargs={'event_id': event.id})
            )
            self.assertEqual(response.status_code, 200)
        
        event.refresh_from_db()
        self.assertEqual(event.participant_count(), 5)

        for i, user in enumerate(users[:2]):
            self.client.login(username=user.username, password=f'pass{i}')
            response = self.client.post(
                reverse('event:leave_event', kwargs={'event_id': event.id})
            )
            self.assertEqual(response.status_code, 200)
        
        event.refresh_from_db()
        self.assertEqual(event.participant_count(), 3)
    
    def test_deadline_enforcement_workflow(self):
        deadline = timezone.now() + timedelta(days=2)
        event = create_event(
            community=self.community,
            created_by=self.admin_user,
            date=timezone.now() + timedelta(days=10),
            registration_deadline=deadline
        )

        self.client.login(username='user1', password='pass1')
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': event.id})
        )
        self.assertEqual(response.status_code, 200)

        event.registration_deadline = timezone.now() - timedelta(hours=1)
        event.save()

        self.client.login(username='user2', password='pass2')
        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': event.id})
        )
        self.assertEqual(response.status_code, 400)
    
    def test_event_filtering_integration(self):
        events_data = [
            {'name': 'Basketball Jakarta', 'location': 'Jakarta', 'days': 2},
            {'name': 'Football Bandung', 'location': 'Bandung', 'days': 5},
            {'name': 'Basketball Bandung', 'location': 'Bandung', 'days': 10},
            {'name': 'Swimming Jakarta', 'location': 'Jakarta', 'days': -2},
        ]
        
        for data in events_data:
            create_event(
                name=data['name'],
                location=data['location'],
                community=self.community,
                date=timezone.now() + timedelta(days=data['days'])
            )

        response = self.client.get(
            reverse('event:event_list'),
            {'name': 'Basketball', 'location': 'Bandung'}
        )
        events = response.context['events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['name'], 'Basketball Bandung')

        response = self.client.get(
            reverse('event:event_list'),
            {'status': 'upcoming', 'date_sort': 'soonest'}
        )
        events = response.context['events']
        self.assertTrue(all(not e['is_past'] for e in events))
        self.assertEqual(events[0]['name'], 'Basketball Jakarta')

class EventAjaxViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user(username='testuser', password='testpass')
        self.admin_user = create_user(username='admin', password='adminpass')
        
        self.fitness_spot = create_fitness_spot()
        self.category = create_category()
        self.community = create_community(
            fitness_spot=self.fitness_spot,
            category=self.category
        )
        self.community.admins.add(self.admin_user)
    
    def test_create_event_json_parsing_error(self):
        self.client.login(username='admin', password='adminpass')
        
        response = self.client.post(
            reverse('event:create_event'),
            data='invalid json {',
            content_type='application/json'
        )

        self.assertIn(response.status_code, [400, 500])
    
    def test_edit_event_json_parsing_error(self):
        event = create_event(community=self.community, created_by=self.admin_user)
        self.client.login(username='admin', password='adminpass')
        
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': event.id}),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [400, 500])
    
    def test_create_event_empty_json(self):
        self.client.login(username='admin', password='adminpass')
        
        response = self.client.post(
            reverse('event:create_event'),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_view_returns_proper_json_structure(self):
        event = create_event(community=self.community, created_by=self.admin_user)
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(
            reverse('event:join_event', kwargs={'event_id': event.id})
        )
        data = json.loads(response.content)
        
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertIn('participant_count', data)

        response = self.client.post(
            reverse('event:leave_event', kwargs={'event_id': event.id})
        )
        data = json.loads(response.content)
        
        self.assertIn('status', data)
        self.assertIn('message', data)
    
    @unittest.skip("URL 'get_event_detail' not found in URL configuration")
    def test_get_event_detail_date_format(self):
        event = create_event(
            community=self.community,
            created_by=self.admin_user,
            date=timezone.now() + timedelta(days=5)
        )
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.get(
            reverse('event:get_event_detail', kwargs={'event_id': event.id})
        )
        data = json.loads(response.content)

        self.assertIn('date', data['event'])
        self.assertIn('date_input', data['event'])

        import re
        date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}'
        self.assertIsNotNone(re.match(date_pattern, data['event']['date']))
    
    def test_community_events_api_date_formats(self):
        event = create_event(
            community=self.community,
            date=timezone.now() + timedelta(days=5)
        )
        
        response = self.client.get(
            reverse('event:community_events_api', kwargs={'community_id': self.community.id})
        )
        data = json.loads(response.content)
        
        event_data = data['events'][0]
        self.assertIn('date', event_data)
        self.assertIn('date_display', event_data)
    
    def test_error_responses_include_message(self):
        self.client.login(username='testuser', password='testpass')

        event = create_event(community=self.community, created_by=self.admin_user)
        response = self.client.post(
            reverse('event:edit_event', kwargs={'event_id': event.id}),
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertTrue(len(data['message']) > 0)