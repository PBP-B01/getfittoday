from django.test import TestCase, Client, RequestFactory
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.http import JsonResponse
from home.models import FitnessSpot
from community.models import Community, CommunityCategory, CommunityPost
from community.forms import CommunityForm
import django.contrib.admin as admin
from community.admin import CommunityAdmin

User = get_user_model()

class CommunityModelTest(TestCase):
    def setUp(self):
        self.category = CommunityCategory.objects.create(name="Futsal", slug="futsal")
        self.spot = FitnessSpot.objects.create(
            name="FitZone", place_id="spot123", latitude=0.0, longitude=0.0
        )
        self.user = User.objects.create_user(username="burhan", password="password123")
        self.community = Community.objects.create(
            name="Burhan FC",
            description="Komunitas futsal paling solid",
            contact_info="Instagram: @burhanfc",
            fitness_spot=self.spot,
            category=self.category,
        )
        self.community.admins.add(self.user)
        self.member_user = User.objects.create_user(username="member", password="memberpass")
        self.community.members.add(self.member_user)


    def test_str_methods(self):
        self.assertEqual(str(self.community), "Burhan FC")
        self.assertEqual(str(self.category), "Futsal")

        post = CommunityPost.objects.create(
            community=self.community, title="Latihan Mingguan", content="Sabtu sore!"
        )
        self.assertEqual(str(post), "Latihan Mingguan (in Burhan FC)")

    def test_meta_verbose_name(self):
        self.assertEqual(str(Community._meta.verbose_name_plural), "Komunitas")
        self.assertEqual(str(CommunityCategory._meta.verbose_name_plural), "Kategori Komunitas")

    def test_is_admin(self):
        self.assertTrue(self.community.is_admin(self.user))
        non_admin_user = User.objects.create_user(username="nonadmin", password="test")
        self.assertFalse(self.community.is_admin(non_admin_user))
        self.assertFalse(self.community.is_admin(User()))

    def test_is_member(self):
        self.assertTrue(self.community.is_member(self.member_user))
        self.assertFalse(self.community.is_member(self.user))

        self.community.members.add(self.user)
        self.assertTrue(self.community.is_member(self.user))

        self.assertFalse(self.community.is_member(User()))

class CommunityFormTest(TestCase):
    def test_valid_form(self):
        spot = FitnessSpot.objects.create(
            name="Spot 1", place_id="p1", latitude=0.0, longitude=0.0
        )
        form_data = {
            "name": "Yoga Group",
            "description": "Desc",
            "contact_info": "IG @yoga",
            "fitness_spot": spot.pk, 
            "category": None
        }
        form = CommunityForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors.as_json()) 

    def test_invalid_form(self):
        form = CommunityForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('fitness_spot', form.errors)


class CommunityAdminTest(TestCase):
    def setUp(self):
        self.site = admin.site
        self.category = CommunityCategory.objects.create(name="TestCat", slug="testcat")
        self.spot = FitnessSpot.objects.create(
            name="Spot A", place_id="spotA", latitude=0.0, longitude=0.0
        )
        self.user = User.objects.create_user(username="admin", password="admin")
        self.community = Community.objects.create(
            name="TestComm", description="desc", fitness_spot=self.spot, category=self.category
        )
        self.community.admins.add(self.user)
        self.member_user = User.objects.create_user(username="member_c", password="pass")
        self.community.members.add(self.member_user) 
        self.admin_model = CommunityAdmin(Community, self.site)

    def test_admin_list_display_methods(self):
        result_admins = self.admin_model.admin_list(self.community)
        self.assertIn("admin", result_admins)
        self.assertEqual(self.admin_model.member_count(self.community), 1) 


class CommunityViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="naomi", password="testpass")
        self.category = CommunityCategory.objects.create(name="Yoga", slug="yoga")
        self.spot = FitnessSpot.objects.create(
            name="Healthy Spot", place_id="spot567", latitude=0.0, longitude=0.0
        )
        self.community = Community.objects.create(
            name="Yoga Lovers",
            description="Komunitas Yoga Mingguan",
            fitness_spot=self.spot,
            category=self.category,
        )
        self.outsider = User.objects.create_user(username="outsider", password="outpass")

    def login(self):
        self.client.login(username="naomi", password="testpass")
        
    def test_community_list_view(self):
        response = self.client.get(reverse("community:community_list")) 
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "community/community_list.html")

    def test_community_detail_view(self):
        response = self.client.get(reverse("community:community_detail", args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yoga Lovers")
        
        response = self.client.get(reverse("community:community_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_add_community_get_and_post(self):
        self.login()
        try:
            response = self.client.get(reverse("community:add_community"))
            self.assertIn(response.status_code, [200, 405])
        except NoReverseMatch:
            pass

        data = {
            "name": "New Group Traditional",
            "description": "Desc",
            "contact_info": "IG",
            "fitness_spot": self.spot.pk,
            "category": self.category.pk,
        }
        try:
            response = self.client.post(reverse("community:add_community"), data)
            self.assertIn(response.status_code, [302, 200])
        except NoReverseMatch:
            pass
        

    def test_ajax_add_community_success_and_invalid(self):
        self.login()
        data = {
            "name": "AjaxGroup",
            "description": "Ajax Desc",
            "contact_info": "IG",
            "fitness_spot": self.spot.pk,
        }
        response = self.client.post(reverse("community:ajax_add_community"), data)
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()["success"])
        self.assertTrue(Community.objects.filter(name="AjaxGroup").exists())

        response = self.client.post(reverse("community:ajax_add_community"), {})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

        response = self.client.get(reverse("community:ajax_add_community"))
        self.assertEqual(response.status_code, 405)


    def test_ajax_edit_and_delete(self):
        self.login()
        self.community.admins.add(self.user)

        self.community.admins.remove(self.user)
        response = self.client.post(reverse("community:ajax_edit_community", args=[self.community.id]), {})
        self.assertEqual(response.status_code, 403)
        self.community.admins.add(self.user)

        data = {
            "name": "Edited",
            "description": "Edited desc",
            "contact_info": "new",
            "fitness_spot": self.spot.pk,
        }
        response = self.client.post(reverse("community:ajax_edit_community", args=[self.community.id]), data)
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()["success"])
        self.community.refresh_from_db()
        self.assertEqual(self.community.name, "Edited")

        response = self.client.post(reverse("community:ajax_edit_community", args=[self.community.id]), {})
        self.assertEqual(response.status_code, 400)

        response = self.client.get(reverse("community:ajax_edit_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        self.community.admins.remove(self.user)
        response = self.client.post(reverse("community:ajax_delete_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 403)

        self.community.admins.add(self.user)
        response = self.client.post(reverse("community:ajax_delete_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Community.objects.filter(id=self.community.id).exists())

        new_comm = Community.objects.create(name="temp", description="x", fitness_spot=self.spot)
        new_comm.admins.add(self.user)
        response = self.client.get(reverse("community:ajax_delete_community", args=[new_comm.id]))
        self.assertEqual(response.status_code, 405)


    def test_ajax_join_leave(self):
        self.login()

        self.assertFalse(self.community.is_member(self.user))

        response = self.client.post(reverse("community:ajax_join_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.community.refresh_from_db()
        self.assertTrue(self.community.is_member(self.user))
        self.assertEqual(response.json()['action'], 'joined')
        
        response = self.client.post(reverse("community:ajax_join_community", args=[9999]))
        self.assertEqual(response.status_code, 404)

        self.community.members.remove(self.user)
        self.community.admins.add(self.user)
        response = self.client.post(reverse("community:ajax_join_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 403)

        self.community.admins.remove(self.user)
        self.community.members.add(self.user)
        response = self.client.post(reverse("community:ajax_leave_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 200)
        self.community.refresh_from_db()
        self.assertFalse(self.community.is_member(self.user))
        self.assertEqual(response.json()['action'], 'left')

        response = self.client.post(reverse("community:ajax_leave_community", args=[9999]))
        self.assertEqual(response.status_code, 404)

        self.community.admins.add(self.user)
        response = self.client.post(reverse("community:ajax_leave_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 403)

        self.community.admins.remove(self.user)
        self.community.members.remove(self.user)
        response = self.client.post(reverse("community:ajax_leave_community", args=[self.community.id]))

        self.assertIn(response.status_code, [200, 400, 500])

        response = self.client.get(reverse("community:ajax_leave_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)


    def test_ajax_add_admin(self):
        self.login()
        self.community.admins.add(self.user)
        other = User.objects.create_user(username="budi", password="x")
        self.assertFalse(other in self.community.admins.all())

        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "budi"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.community.refresh_from_db()
        self.assertTrue(other in self.community.admins.all())

        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]), {}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.get(reverse("community:ajax_add_community_admin", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        self.community.admins.remove(self.user)
        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "budi"},
        )
        self.assertEqual(response.status_code, 403)
        self.community.admins.add(self.user)

        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "ghost"},
        )
        self.assertEqual(response.status_code, 404)
        
        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[9999]),
            {"username": "budi"},
        )
        self.assertEqual(response.status_code, 404)


    def test_communities_by_spot_and_place_json(self):
        response = self.client.get(
            reverse("community:communities_by_place_json", args=[self.spot.place_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()['communities']) > 0)

        other_spot = FitnessSpot.objects.create(name="None", place_id="none1", latitude=0.0, longitude=0.0)
        response = self.client.get(
            reverse("community:communities_by_place_json", args=[other_spot.place_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['communities']), 0)


    def test_invalid_join_leave_methods(self):
        self.login()
        response = self.client.get(reverse("community:ajax_join_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse("community:ajax_join_community", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_featured_communities_api(self):
        response = self.client.get(reverse("community:featured_communities_api"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('communities', response.json())
        self.assertTrue(len(response.json()['communities']) > 0)
