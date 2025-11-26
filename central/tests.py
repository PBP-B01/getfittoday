import json 
from unittest.mock import patch 
from django.test import TestCase, Client 
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from central.models import Admin 
from central.admin import AdminChangeForm
from central import views
from django.test.utils import override_settings

User = get_user_model()

class AdminModelTest(TestCase):
    """Tests the custom Admin model's password and signal logic."""

    def setUp(self):
        self.admin = Admin.objects.create(name="testadmin")
        self.admin.set_password("securepassword")
        self.admin.save()

    def test_set_and_check_password(self):
        """Test that set_password hashes the password and check_password verifies it."""
        self.assertNotEqual(self.admin.password, "securepassword")
        self.assertTrue(self.admin.password.startswith('pbkdf2_sha256$'))

        self.assertTrue(self.admin.check_password("securepassword"))

        self.assertFalse(self.admin.check_password("wrongpassword"))

    @override_settings(MIGRATION_MODULES={'store': None})
    @patch('central.views.create_default_admin') 
    def test_create_default_admin_signal(self, mock_create_default_admin):
        """Test that the post_migrate signal creates the default 'Agil' admin."""
        Admin.objects.filter(name="Agil").delete()
        
        from central.models import create_default_admin
        create_default_admin(sender=type('FakeAppConfig', (object,), {'name': 'store'}))

        default_admin = Admin.objects.get(name="Agil")
        self.assertIsNotNone(default_admin)
        self.assertTrue(default_admin.check_password("Agil123"))

class AdminFormTest(TestCase):
    """Tests the custom AdminChangeForm logic."""

    def setUp(self):
        self.admin_user = Admin.objects.create(name="initial_admin")
        self.admin_user.set_password("oldpassword")
        self.admin_user.save()
        self.initial_hash = self.admin_user.password

    def test_form_save_new_password(self):
        """Test saving the form with a new password hashes the password."""
        data = {'name': 'initial_admin', 'password': 'newpassword'}
        form = AdminChangeForm(data, instance=self.admin_user)
        self.assertTrue(form.is_valid())
        
        admin_instance = form.save()
        admin_instance.refresh_from_db()
        
        self.assertNotEqual(admin_instance.password, self.initial_hash)
        self.assertTrue(check_password('newpassword', admin_instance.password))

    def test_form_save_no_password_change(self):
        """Test saving the form without providing a password preserves the old hash."""
        data = {'name': 'initial_admin', 'password': ''}
        form = AdminChangeForm(data, instance=self.admin_user)
        self.assertTrue(form.is_valid())
        admin_instance = form.save()
        admin_instance.refresh_from_db()
        self.assertEqual(admin_instance.password, '') 

class AuthViewTest(TestCase):
    """Tests the login_ajax and register_ajax view logic."""
    def setUp(self):
        self.client = Client() 
        self.user = User.objects.create_user(username="testuser", password="userpass")
        self.admin_user = Admin.objects.create(name="testadmin")
        self.admin_user.set_password("adminpass")
        self.admin_user.save()

    def test_login_ajax_standard_user_success(self):
        """Test successful login for a standard Django user."""
        data = {'username': 'testuser', 'password': 'userpass'}
        response = self.client.post(reverse('central:login_ajax'), data) 
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            "ok": True, 
            "redirect": "/", 
            "username": "testuser", 
            "role": "user"
        })
        self.assertFalse(self.client.session.get("is_admin"))

    def test_login_ajax_custom_admin_success(self):
        """Test successful login for a custom Admin user."""
        data = {'username': 'testadmin', 'password': 'adminpass'}
        response = self.client.post(reverse('central:login_ajax'), data) 
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            "ok": True, 
            "redirect": "/", 
            "username": "testadmin", 
            "role": "admin"
        })
        self.assertTrue(self.client.session.get("is_admin"))
        self.assertEqual(self.client.session.get("admin_name"), "testadmin")

    def test_login_ajax_failure(self):
        """Test login failure with incorrect credentials."""
        data = {'username': 'testuser', 'password': 'wrongpass'}
        response = self.client.post(reverse('central:login_ajax'), data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username atau password salah", response.content.decode())

    def test_logout_ajax(self):
        """Test successful logout."""
        self.client.login(username='testuser', password='userpass')
        response = self.client.post(reverse('central:logout_ajax'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"ok": True, "redirect": "/"})
        self.assertIsNone(self.client.session.get('_auth_user_id')) 

    def test_register_ajax_success(self):
        """Test successful user registration."""
        new_username = "newuser"
        new_password = "newpassword"
        data = {
            'username': new_username, 
            'password': new_password, 
            'password2': new_password 
        }
        response = self.client.post(reverse('central:register_ajax'), data)
        self.assertEqual(response.status_code, 302) 
        self.assertEqual(response.url, views._login_url())
        self.assertTrue(User.objects.filter(username=new_username).exists())

    def test_register_ajax_failure(self):
        """Test registration failure due to invalid data (e.g., weak password)."""
        data = {'username': 'short', 'password': '1', 'password2': '1'}
        response = self.client.post(reverse('central:register_ajax'), data)
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['ok'])
        self.assertIn('password', json_response['errors'])

class HelperFunctionTest(TestCase):
    """Tests the _home_url and _login_url helper functions."""
    def test_home_url_no_reverse(self):
        """Test _home_url returns '/' when 'home:home' is not found."""
        self.assertEqual(views._home_url(), "/")

    @override_settings(LOGIN_URL="/custom-login/")
    def test_login_url_custom_setting(self):
        """Test _login_url finds the LOGIN_URL setting."""
        self.assertEqual(views._login_url(), reverse("central:login"))
    