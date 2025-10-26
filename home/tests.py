import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.models import User
from django.http import QueryDict
from django.contrib.admin.sites import AdminSite
from .models import PlaceType, FitnessSpot
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from .views import get_grid_bounds, GRID_ORIGIN_LAT, GRID_ORIGIN_LNG, GRID_CELL_SIZE_DEG
import json
from unittest import mock
from django.test import TestCase, Client, override_settings
from django.http import Http404
from .views import get_grid_bounds, GRID_ORIGIN_LAT, GRID_ORIGIN_LNG, GRID_CELL_SIZE_DEG


try:
    from community.models import Community
except ImportError:
    class MockCommunity:
        objects = MagicMock()
        _id_counter = 1
        def __init__(self, **kwargs):
            self.id = MockCommunity._id_counter
            MockCommunity._id_counter += 1
            self.__dict__.update(kwargs)

        @classmethod
        def create(cls, **kwargs):
            return cls(**kwargs)

    Community = MockCommunity

class HomeSetupMixin(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

        self.type_gym = PlaceType.objects.create(name='gym')
        self.type_pool = PlaceType.objects.create(name='swimming_pool')

        self.spot1 = FitnessSpot.objects.create(
            place_id='place_A', name='Spot Populer', address='Jl. Sudirman',
            latitude=Decimal('-6.75'), longitude=Decimal('106.55'),
            rating=Decimal('4.5'), rating_count=150
        )
        self.spot1.types.add(self.type_gym, self.type_pool)
        self.spot1.save()

        self.spot2 = FitnessSpot.objects.create(
            place_id='place_B', name='Spot Biasa', address='Jl. Gatot Subroto',
            latitude=Decimal('-6.78'), longitude=Decimal('106.58'),
            phone_number='123456', website='http://biasa.com',
            rating=Decimal('3.8'), rating_count=50
        )
        self.spot2.types.add(self.type_gym)
        self.spot2.save()

        self.spot_max_lat = FitnessSpot.objects.create(
            place_id='place_MAX_LAT', name='Spot Max Lat', address='Jl. Utara',
            latitude=Decimal('-6.0'), longitude=Decimal('106.50'), rating_count=1
        )
        self.spot_min_lat = FitnessSpot.objects.create(
            place_id='place_MIN_LAT', name='Spot Min Lat', address='Jl. Selatan',
            latitude=Decimal('-7.0'), longitude=Decimal('106.50'), rating_count=1
        )
        self.spot_max_lng = FitnessSpot.objects.create(
            place_id='place_MAX_LNG', name='Spot Max Lng', address='Jl. Timur',
            latitude=Decimal('-6.50'), longitude=Decimal('108.0'), rating_count=1
        )
        self.spot_min_lng = FitnessSpot.objects.create(
            place_id='place_MIN_LNG', name='Spot Min Lng', address='Jl. Barat',
            latitude=Decimal('-6.50'), longitude=Decimal('105.0'), rating_count=1
        )

class HomeModelsTests(HomeSetupMixin):
    def test_place_type_str(self):
        self.assertEqual(str(self.type_gym), 'gym')

    def test_fitness_spot_str(self):
        self.assertEqual(str(self.spot1), 'Spot Populer')

    def test_signal_pre_delete_place_type(self):
        self.type_pool.delete()
        self.assertIsNone(FitnessSpot.objects.filter(place_id='place_A').first())

class HomeFormsTests(TestCase):
    def test_styled_user_creation_form_widgets(self):
        form = StyledUserCreationForm()
        self.assertEqual(form.fields["username"].widget.attrs["placeholder"], "Username")

    def test_styled_authentication_form_widgets(self):
        form = StyledAuthenticationForm()
        self.assertEqual(form.fields["password"].widget.attrs["placeholder"], "Password")

class StyledFormsTest(TestCase):
    def test_user_creation_form_fields(self):
        """Test StyledUserCreationForm fields and widget attributes."""
        form = StyledUserCreationForm()
        self.assertIn("username", form.fields)
        self.assertIn("password1", form.fields)
        self.assertIn("password2", form.fields)

        self.assertIn("Username", form.fields["username"].widget.attrs["placeholder"])
        self.assertIn("Password", form.fields["password1"].widget.attrs["placeholder"])
        self.assertIn("Ulangi password", form.fields["password2"].widget.attrs["placeholder"])
        self.assertIn("w-full", form.fields["username"].widget.attrs["class"])

    def test_authentication_form_fields(self):
        """Test StyledAuthenticationForm fields and widget attributes."""
        form = StyledAuthenticationForm()
        self.assertIn("username", form.fields)
        self.assertIn("password", form.fields)

        self.assertIn("Username", form.fields["username"].widget.attrs["placeholder"])
        self.assertIn("Password", form.fields["password"].widget.attrs["placeholder"])
        self.assertIn("w-full", form.fields["username"].widget.attrs["class"])

    def test_user_creation_form_validation(self):
        """Test valid and invalid form submissions."""
        form_data = {"username": "testuser", "password1": "Secret123!", "password2": "Secret123!"}
        form = StyledUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data_invalid = {"username": "testuser2", "password1": "Secret123!", "password2": "WrongPass!"}
        form_invalid = StyledUserCreationForm(data=form_data_invalid)
        self.assertFalse(form_invalid.is_valid())
        self.assertIn("password2", form_invalid.errors)

    def test_authentication_form_validation(self):
        """Test StyledAuthenticationForm login validation."""
        user = User.objects.create_user(username="testuser", password="Secret123!")
        
        form_data = {"username": "testuser", "password": "Secret123!"}
        form = StyledAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data_invalid = {"username": "testuser", "password": "WrongPass!"}
        form_invalid = StyledAuthenticationForm(data=form_data_invalid)
        self.assertFalse(form_invalid.is_valid())
        self.assertIn("__all__", form_invalid.errors)  

import json
from unittest import mock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache

from .views import get_grid_bounds, GRID_ORIGIN_LAT, GRID_ORIGIN_LNG, GRID_CELL_SIZE_DEG

class GridBoundsUtilTest(TestCase):
    """
    Tests the get_grid_bounds helper function in isolation.
    """
    def test_get_grid_bounds_valid(self):
        grid_id = '3-5'
        
        expected_sw_lat = GRID_ORIGIN_LAT + 3 * GRID_CELL_SIZE_DEG
        expected_sw_lng = GRID_ORIGIN_LNG + 5 * GRID_CELL_SIZE_DEG
        expected_ne_lat = expected_sw_lat + GRID_CELL_SIZE_DEG
        expected_ne_lng = expected_sw_lng + GRID_CELL_SIZE_DEG
        
        bounds = get_grid_bounds(grid_id)
        
        self.assertIsNotNone(bounds)
        self.assertAlmostEqual(bounds['sw_lat'], expected_sw_lat)
        self.assertAlmostEqual(bounds['sw_lng'], expected_sw_lng)
        self.assertAlmostEqual(bounds['ne_lat'], expected_ne_lat)
        self.assertAlmostEqual(bounds['ne_lng'], expected_ne_lng)

    def test_get_grid_bounds_invalid_format(self):
        """Tests the error handling for invalid grid ID formats."""
        self.assertIsNone(get_grid_bounds('foo-bar'))
        self.assertIsNone(get_grid_bounds('1'))

@override_settings(GOOGLE_MAPS_API_KEY='TEST_API_KEY')
class HomeViewsTest(TestCase):
    """
    Tests all views in views.py with mocks for external dependencies.
    """
    def setUp(self):
        self.client = Client()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_home_view(self):
        response = self.client.get(reverse('home:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')
        self.assertEqual(response.context['google_api_key'], 'TEST_API_KEY')

    def test_get_fitness_spots_data_no_grid_id(self):
        response = self.client.get(reverse('home:get_fitness_spots_data_api'))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'gridId parameter is required')

    def test_get_fitness_spots_data_invalid_grid_id(self):
        response = self.client.get(reverse('home:get_fitness_spots_data_api'), {'gridId': 'foo-bar'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Invalid gridId format')

    @mock.patch('home.views.cache')
    def test_get_fitness_spots_data_cache_hit(self, mock_cache):
        grid_id = '3-5'
        cached_data = {'spots': [{'name': 'Cached Spot', 'place_id': '123'}]}
        mock_cache.get.return_value = cached_data
        
        response = self.client.get(reverse('home:get_fitness_spots_data_api'), {'gridId': grid_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, cached_data)
        mock_cache.get.assert_called_with(f"spots_grid_{grid_id}")

    @mock.patch('home.views.cache')
    @mock.patch('home.views.FitnessSpot.objects')
    def test_get_fitness_spots_data_cache_miss(self, mock_spot_objects, mock_cache):
        grid_id = '3-5'
        mock_cache.get.return_value = None  

        mock_db_data = [
            {'place_id': '1', 'name': 'Spot 1', 'types__name': 'Gym', 'latitude': -6.1, 'longitude': 106.8,
             'address': 'A', 'rating': 5, 'rating_count': 100, 'website': 'a.com', 'phone_number': '123'},
            {'place_id': '1', 'name': 'Spot 1', 'types__name': 'Park', 'latitude': -6.1, 'longitude': 106.8,
             'address': 'A', 'rating': 5, 'rating_count': 100, 'website': 'a.com', 'phone_number': '123'},
            {'place_id': '2', 'name': 'Spot 2', 'types__name': 'Studio', 'latitude': -6.2, 'longitude': 106.9,
             'address': 'B', 'rating': 4, 'rating_count': 50, 'website': 'b.com', 'phone_number': '456'},
            {'place_id': '3', 'name': 'Spot 3', 'types__name': None, 'latitude': -6.3, 'longitude': 106.7,
             'address': 'C', 'rating': 3, 'rating_count': 10, 'website': 'c.com', 'phone_number': '789'},
        ]
        
        mock_spot_objects.filter.return_value.values.return_value = mock_db_data

        response = self.client.get(reverse('home:get_fitness_spots_data_api'), {'gridId': grid_id})
        self.assertEqual(response.status_code, 200)

        mock_spot_objects.filter.assert_called_once()
        data = json.loads(response.content)
        self.assertEqual(len(data['spots']), 3)
        spot1 = next(s for s in data['spots'] if s['place_id'] == '1')
        spot2 = next(s for s in data['spots'] if s['place_id'] == '2')
        spot3 = next(s for s in data['spots'] if s['place_id'] == '3')
        self.assertCountEqual(spot1['types'], ['Gym', 'Park'])
        self.assertCountEqual(spot2['types'], ['Studio'])
        self.assertCountEqual(spot3['types'], [])
        mock_cache.set.assert_called_once_with(f"spots_grid_{grid_id}", data, 60 * 60 * 24)

    @mock.patch('home.views.cache')
    def test_get_map_boundaries_cache_hit(self, mock_cache):
        cached_data = {'north': 1.0, 'south': -1.0, 'east': 1.0, 'west': -1.0}
        mock_cache.get.return_value = cached_data
        
        response = self.client.get(reverse('home:get_map_boundaries'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, cached_data)
        mock_cache.get.assert_called_with('map_boundaries')

    @mock.patch('home.views.cache')
    @mock.patch('home.views.FitnessSpot.objects')
    def test_get_map_boundaries_cache_miss(self, mock_spot_objects, mock_cache):
        mock_cache.get.return_value = None
        mock_db_bounds = {'min_lat': -6.5, 'max_lat': -6.0, 'min_lng': 106.0, 'max_lng': 107.0}
        mock_spot_objects.aggregate.return_value = mock_db_bounds
        
        expected_response = {'north': -6.0, 'south': -6.5, 'east': 107.0, 'west': 106.0}
        response = self.client.get(reverse('home:get_map_boundaries'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, expected_response)
        mock_spot_objects.aggregate.assert_called_once()
        mock_cache.set.assert_called_once_with('map_boundaries', expected_response, 60 * 60 * 24 * 7)

    @mock.patch('home.views.cache')
    @mock.patch('home.views.FitnessSpot.objects')
    def test_get_map_boundaries_no_spots(self, mock_spot_objects, mock_cache):
        mock_cache.get.return_value = None
        mock_spot_objects.aggregate.return_value = {'min_lat': None, 'max_lat': None, 'min_lng': None, 'max_lng': None}
        
        response = self.client.get(reverse('home:get_map_boundaries'))
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'No spots found')

    @mock.patch('home.views.Community.objects')
    @mock.patch('home.views.get_object_or_404')
    def test_communities_by_place_found(self, mock_get_obj, mock_comm_objects):
        place_id = 'test-place-id'
        mock_spot = mock.MagicMock(name='MockSpot')
        mock_get_obj.return_value = mock_spot
        mock_db_comms = [{'id': 1, 'name': 'Comm 1', 'description': 'Desc 1'},
                         {'id': 2, 'name': 'Comm 2', 'description': 'Desc 2'}]
        mock_comm_objects.filter.return_value.values.return_value = mock_db_comms
        
        response = self.client.get(reverse('home:communities_by_place', args=[place_id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'communities': mock_db_comms})
        mock_get_obj.assert_called_once()
        mock_comm_objects.filter.assert_called_once_with(fitness_spot=mock_spot)

    @mock.patch('home.views.get_object_or_404')
    def test_communities_by_place_not_found(self, mock_get_obj):
        mock_get_obj.side_effect = Http404
        
        response = self.client.get(reverse('home:communities_by_place', args=['not-found']))
        
        self.assertEqual(response.status_code, 404)

class AdminTests(HomeSetupMixin):
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        from .admin import FitnessSpotAdmin, PlaceTypeAdmin
        self.fsa = FitnessSpotAdmin(FitnessSpot, self.site)
        self.pta = PlaceTypeAdmin(PlaceType, self.site)

    def test_fitness_spot_admin_list_display(self):
        self.assertEqual(self.fsa.list_display, ('name', 'address', 'rating', 'rating_count'))

    def test_admin_filter_types(self):
        mock_request = MagicMock(user=MagicMock(is_active=True, is_staff=True))
        mock_request.GET = QueryDict('types__name__exact=gym', mutable=True)
        changelist = self.fsa.get_changelist_instance(mock_request)
        queryset = changelist.get_queryset(mock_request)
        self.assertEqual(queryset.count(), 2)  
