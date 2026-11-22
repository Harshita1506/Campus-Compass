from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from notifications.models import Notification
from roommates.compatibility import WEIGHTS, compatibility
from roommates.models import RoommateProfile, RoommateRequest
from tests.helpers import make_user


def profile(**kw):
    base = dict(budget_min=6000, budget_max=9000, preferred_location="north_gate", food_preference="veg",
                sleep_schedule="early", cleanliness=3)
    base.update(kw)
    return SimpleNamespace(**base)


class CompatibilityAlgorithmTests(SimpleTestCase):
    def test_weights_sum_to_100(self):
        self.assertEqual(sum(WEIGHTS.values()), 100)
        self.assertEqual(WEIGHTS, {"budget": 30, "location": 25, "food": 15, "sleep": 15, "cleanliness": 15})

    def test_identical_profiles_score_100(self):
        result = compatibility(profile(), profile())
        self.assertEqual(result["score"], 100)
        self.assertEqual(len(result["matching"]), 5)

    def test_completely_different_profiles_score_low(self):
        other = profile(budget_min=20000, budget_max=25000, preferred_location="city_centre",
                        food_preference="nonveg", sleep_schedule="night", cleanliness=1)
        result = compatibility(profile(), other)
        self.assertLess(result["score"], 15)
        self.assertEqual(result["matching"], [])

    def test_partial_match_breakdown(self):
        other = profile(sleep_schedule="night")  # everything matches except sleep
        result = compatibility(profile(), other)
        self.assertEqual(result["score"], 85)
        self.assertEqual(result["breakdown"]["sleep"], 0)
        self.assertNotIn("Sleep schedule", result["matching"])

    def test_symmetric(self):
        a, b = profile(), profile(food_preference="egg", cleanliness=2, budget_min=8000, budget_max=12000)
        self.assertEqual(compatibility(a, b)["score"], compatibility(b, a)["score"])


class RoommateViewTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user("alice"), make_user("bob")
        self.pa = RoommateProfile.objects.create(user=self.a, headline="A", budget_min=5000, budget_max=8000,
                                                 preferred_location="north_gate", accommodation_type="flat",
                                                 food_preference="veg", sleep_schedule="early", cleanliness=3)
        self.pb = RoommateProfile.objects.create(user=self.b, headline="B", budget_min=6000, budget_max=9000,
                                                 preferred_location="north_gate", accommodation_type="pg",
                                                 food_preference="nonveg", sleep_schedule="night", cleanliness=1)

    def test_budget_validation(self):
        self.client.force_login(make_user("carol"))
        self.client.post(reverse("roommates:my_profile"), {
            "headline": "C", "budget_min": 9000, "budget_max": 5000, "preferred_location": "any",
            "accommodation_type": "flat", "food_preference": "veg", "sleep_schedule": "early", "cleanliness": 2,
            "is_active": "on"})
        self.assertFalse(RoommateProfile.objects.filter(headline="C").exists())

    def test_filter_api_returns_compatibility(self):
        self.client.force_login(self.a)
        data = self.client.get(reverse("roommates:api_filter")).json()
        self.assertEqual(data["count"], 1)  # own profile excluded
        self.assertIsInstance(data["results"][0]["compatibility"], int)
        data = self.client.get(reverse("roommates:api_filter"), {"accommodation": "flat"}).json()
        self.assertEqual(data["count"], 0)

    def test_send_accept_request_flow(self):
        self.client.force_login(self.a)
        self.client.post(reverse("roommates:send_request", args=[self.pb.pk]), {"message": "Hi"})
        self.client.post(reverse("roommates:send_request", args=[self.pb.pk]), {"message": "Hi again"})
        self.assertEqual(RoommateRequest.objects.count(), 1)  # no duplicate pending
        req = RoommateRequest.objects.get()
        self.assertTrue(Notification.objects.filter(recipient=self.b, notification_type="roommate_request").exists())
        # sender cannot accept own request
        self.assertEqual(self.client.post(reverse("roommates:respond", args=[req.pk, "accept"])).status_code, 403)
        self.client.force_login(self.b)
        self.client.post(reverse("roommates:respond", args=[req.pk, "accept"]))
        req.refresh_from_db()
        self.assertEqual(req.status, "accepted")
        self.assertTrue(Notification.objects.filter(recipient=self.a, notification_type="request_accepted").exists())

    def test_reject_via_ajax(self):
        req = RoommateRequest.objects.create(sender=self.a, receiver=self.b)
        self.client.force_login(self.b)
        r = self.client.post(reverse("roommates:respond", args=[req.pk, "reject"]),
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json()["status"], "rejected")

    def test_save_profile_toggle(self):
        self.client.force_login(self.a)
        url = reverse("roommates:api_save", args=[self.pb.pk])
        self.assertTrue(self.client.post(url).json()["saved"])
        self.assertIn(self.pb, self.a.saved_roommates.all())
        self.assertFalse(self.client.post(url).json()["saved"])
