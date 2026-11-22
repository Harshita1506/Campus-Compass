from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from lostfound.matching import record_matches, score_pair
from lostfound.models import Item, ItemMatch
from notifications.models import Notification
from tests.helpers import make_item, make_user


class LostFoundCrudTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.other = make_user("other")

    def test_create_item(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("lostfound:create"), {
            "item_type": "lost", "title": "Red umbrella", "category": "other", "description": "Folding umbrella",
            "location": "Cafeteria", "date": date.today().isoformat()})
        item = Item.objects.get(title="Red umbrella")
        self.assertRedirects(response, item.get_absolute_url())
        self.assertEqual(item.owner, self.owner)

    def test_future_date_rejected(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("lostfound:create"), {
            "item_type": "lost", "title": "X", "category": "other", "description": "x", "location": "y",
            "date": (date.today() + timedelta(days=3)).isoformat()})
        self.assertFalse(Item.objects.exists())

    def test_only_owner_can_edit_or_delete(self):
        item = make_item(self.owner)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("lostfound:edit", args=[item.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("lostfound:delete", args=[item.pk])).status_code, 403)
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())
        self.client.force_login(self.owner)
        self.client.post(reverse("lostfound:delete", args=[item.pk]))
        self.assertFalse(Item.objects.filter(pk=item.pk).exists())

    def test_mark_recovered_ajax(self):
        item = make_item(self.owner)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("lostfound:api_status", args=[item.pk]),
                                          {"status": "recovered"}).status_code, 403)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("lostfound:api_status", args=[item.pk]), {"status": "recovered"})
        self.assertEqual(response.json()["status"], "recovered")
        item.refresh_from_db()
        self.assertEqual(item.status, "recovered")
        self.assertIsNotNone(item.recovered_at)

    def test_search_api(self):
        make_item(self.owner, title="Black leather wallet", category="bags")
        make_item(self.owner, title="Calculator", category="electronics", item_type="found")
        self.client.force_login(self.other)
        data = self.client.get(reverse("lostfound:api_search"), {"q": "wallet"}).json()
        self.assertEqual(data["count"], 1)
        data = self.client.get(reverse("lostfound:api_search"), {"item_type": "found"}).json()
        self.assertEqual(data["results"][0]["title"], "Calculator")
        self.assertIn("html", data)


class MatchingTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user("loser"), make_user("finder")

    def test_similar_items_score_high(self):
        lost = make_item(self.a, title="Black leather wallet", category="bags", location="Library 2nd floor")
        found = make_item(self.b, title="Black wallet", category="bags", location="Library second floor",
                          item_type="found")
        self.assertGreaterEqual(score_pair(lost, found), 70)

    def test_unrelated_items_score_low(self):
        lost = make_item(self.a, title="Laptop charger", category="electronics", location="Hostel",
                         date=date.today() - timedelta(days=30))
        found = make_item(self.b, title="Yoga mat", category="other", location="Sports complex", item_type="found")
        self.assertLess(score_pair(lost, found), 40)

    def test_record_matches_notifies_both_owners_once(self):
        make_item(self.a, title="Silver water bottle", category="bottles", location="Gym")
        found = make_item(self.b, title="Silver bottle", category="bottles", location="Gym", item_type="found")
        record_matches(found)
        record_matches(found)
        self.assertEqual(ItemMatch.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(notification_type="lostfound_match").count(), 2)

    def test_own_items_never_match(self):
        make_item(self.a, title="Keys", category="keys")
        own_found = make_item(self.a, title="Keys", category="keys", item_type="found")
        self.assertEqual(record_matches(own_found), [])
