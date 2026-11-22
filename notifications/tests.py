from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from notifications.utils import notify
from tests.helpers import make_user


class NotificationTests(TestCase):
    def setUp(self):
        self.user, self.other = make_user("nuser"), make_user("nother")
        self.n1 = notify(self.user, "system", "Hello", "World", "/dashboard/")
        self.n2 = notify(self.user, "message", "Msg", "Body")

    def test_no_self_notification(self):
        self.assertIsNone(notify(self.user, "system", "x", actor=self.user))

    def test_unread_count_api(self):
        self.client.force_login(self.user)
        data = self.client.get(reverse("notifications:api_unread")).json()
        self.assertEqual(data["unread"], 2)
        self.assertEqual(len(data["latest"]), 2)

    def test_mark_read_and_all(self):
        self.client.force_login(self.user)
        data = self.client.post(reverse("notifications:api_mark_read", args=[self.n1.pk])).json()
        self.assertEqual(data["unread"], 1)
        self.client.post(reverse("notifications:api_mark_all_read"))
        self.assertFalse(Notification.objects.filter(recipient=self.user, is_read=False).exists())

    def test_cannot_mark_others_notification(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("notifications:api_mark_read", args=[self.n1.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("notifications:open", args=[self.n1.pk])).status_code, 404)
        self.n1.refresh_from_db()
        self.assertFalse(self.n1.is_read)

    def test_open_marks_read_and_redirects_safely(self):
        evil = notify(self.user, "system", "Evil", url="https://evil.example.com/")
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("notifications:open", args=[self.n1.pk])), "/dashboard/",
                             fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse("notifications:open", args=[evil.pk])),
                             reverse("notifications:list"))

    def test_notification_center_page(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("notifications:list")), "Hello")
        self.assertNotContains(self.client.get(reverse("notifications:list"), {"show": "unread"}), "zzz")
