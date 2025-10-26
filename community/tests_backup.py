from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
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


class CommunityFormTest(TestCase):
    def test_valid_form(self):
        spot = FitnessSpot.objects.create(
            name="Spot 1", place_id="p1", latitude=0.0, longitude=0.0
        )
        form_data = {
            "name": "Yoga Group",
            "description": "Desc",
            "contact_info": "IG @yoga",
            "fitness_spot": spot.place_id,
        }
        form = CommunityForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = CommunityForm(data={})
        self.assertFalse(form.is_valid())


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
        self.admin_model = CommunityAdmin(Community, self.site)

    def test_admin_list_display_methods(self):
        result_admins = self.admin_model.admin_list(self.community)
        self.assertIn("admin", result_admins)
        self.assertEqual(self.admin_model.member_count(self.community), 0)


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

    def test_add_community_get_and_post(self):
        self.login()
        response = self.client.get(reverse("community:add_community"))
        self.assertEqual(response.status_code, 200)

        data = {
            "name": "New Group",
            "description": "Desc",
            "contact_info": "IG",
            "fitness_spot": self.spot.place_id,
        }
        response = self.client.post(reverse("community:add_community"), data)
        self.assertEqual(response.status_code, 302)

    def test_ajax_add_community_success_and_invalid(self):
        self.login()
        data = {
            "name": "AjaxGroup",
            "description": "Ajax Desc",
            "contact_info": "IG",
            "fitness_spot": self.spot.place_id,
        }
        response = self.client.post(reverse("community:ajax_add_community"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Invalid form
        response = self.client.post(reverse("community:ajax_add_community"), {})
        self.assertEqual(response.status_code, 400)

        # Invalid method
        response = self.client.get(reverse("community:ajax_add_community"))
        self.assertEqual(response.status_code, 405)

    def test_ajax_edit_and_delete(self):
        self.login()
        self.community.admins.add(self.user)

        data = {
            "name": "Edited",
            "description": "Edited desc",
            "contact_info": "new",
            "fitness_spot": self.spot.place_id,
        }
        response = self.client.post(reverse("community:ajax_edit_community", args=[self.community.id]), data)
        self.assertEqual(response.status_code, 200)

        # invalid form
        response = self.client.post(reverse("community:ajax_edit_community", args=[self.community.id]), {})
        self.assertEqual(response.status_code, 400)

        # invalid method
        response = self.client.get(reverse("community:ajax_edit_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        # delete unauthorized
        self.community.admins.remove(self.user)
        response = self.client.post(reverse("community:ajax_delete_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 403)

        # authorized delete
        self.community.admins.add(self.user)
        response = self.client.post(reverse("community:ajax_delete_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 200)

        # invalid method
        new_comm = Community.objects.create(
            name="temp", description="x", fitness_spot=self.spot
        )
        new_comm.admins.add(self.user)
        response = self.client.get(reverse("community:ajax_delete_community", args=[new_comm.id]))
        self.assertEqual(response.status_code, 405)

    def test_ajax_join_leave(self):
        self.login()
        # join
        response = self.client.post(
            reverse("community:ajax_join_community", args=[self.community.id]),
            {},
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        # admin cannot leave
        self.community.admins.add(self.user)
        response = self.client.post(reverse("community:ajax_leave_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 403)

        # invalid method
        response = self.client.get(reverse("community:ajax_leave_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

    def test_ajax_add_admin(self):
        self.login()
        self.community.admins.add(self.user)
        other = User.objects.create_user(username="budi", password="x")

        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "budi"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # no username
        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]), {}
        )
        self.assertEqual(response.status_code, 400)

        # invalid method
        response = self.client.get(reverse("community:ajax_add_community_admin", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        # permission denied
        self.community.admins.remove(self.user)
        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "budi"},
        )
        self.assertEqual(response.status_code, 403)

        # user not found
        self.community.admins.add(self.user)
        response = self.client.post(
            reverse("community:ajax_add_community_admin", args=[self.community.id]),
            {"username": "ghost"},
        )
        self.assertEqual(response.status_code, 404)

    def test_communities_by_spot_and_place_json(self):
        response = self.client.get(reverse("community:communities_by_spot", args=[self.spot.place_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("community:communities_by_place_json", args=[self.spot.place_id])
        )
        self.assertEqual(response.status_code, 200)

        # trigger exception
        response = self.client.get(reverse("community:communities_by_place_json", args=["unknown"]))
        self.assertIn(response.status_code, [200, 404, 500])


    def test_invalid_join_leave_methods(self):
        self.login()
        # invalid join method
        response = self.client.get(reverse("community:ajax_join_community", args=[self.community.id]))
        self.assertEqual(response.status_code, 405)

        # invalid community id
        response = self.client.post(reverse("community:ajax_join_community", args=[9999]))
        self.assertEqual(response.status_code, 404)
