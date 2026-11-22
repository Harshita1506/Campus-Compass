import json

from django.test import TestCase
from django.urls import reverse

from messaging.models import Conversation, Message
from messaging.services import send_message
from notifications.models import Notification
from tests.helpers import make_user


class MessagingTests(TestCase):
    def setUp(self):
        self.a, self.b, self.intruder = make_user("ann"), make_user("ben"), make_user("eve")
        self.msg = send_message(self.a, self.b, "Hello Ben")
        self.convo = self.msg.conversation

    def test_one_conversation_per_pair(self):
        send_message(self.b, self.a, "Hi Ann")
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(self.convo.messages.count(), 2)

    def test_start_conversation_view(self):
        self.client.force_login(self.a)
        r = self.client.get(reverse("messaging:start", args=[self.b.pk]))
        self.assertRedirects(r, reverse("messaging:conversation", args=[self.convo.pk]))

    def test_participants_can_read(self):
        self.client.force_login(self.b)
        self.assertContains(self.client.get(reverse("messaging:conversation", args=[self.convo.pk])), "Hello Ben")
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.is_read)

    def test_ajax_send_and_poll(self):
        self.client.force_login(self.b)
        r = self.client.post(reverse("messaging:api_send", args=[self.convo.pk]), json.dumps({"body": "Hey Ann"}),
                             content_type="application/json")
        self.assertTrue(r.json()["ok"])
        self.client.force_login(self.a)
        data = self.client.get(reverse("messaging:api_messages", args=[self.convo.pk]), {"after": self.msg.pk}).json()
        self.assertEqual([m["body"] for m in data["messages"]], ["Hey Ann"])
        self.assertFalse(data["messages"][0]["mine"])

    def test_empty_message_rejected(self):
        self.client.force_login(self.a)
        r = self.client.post(reverse("messaging:api_send", args=[self.convo.pk]), json.dumps({"body": "   "}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_message_notification_created_and_not_spammed(self):
        send_message(self.a, self.b, "Second")
        self.assertEqual(Notification.objects.filter(recipient=self.b, notification_type="message").count(), 1)

    def test_csrf_enforced_on_send(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        r = client.post(reverse("messaging:api_send", args=[self.convo.pk]), json.dumps({"body": "x"}),
                        content_type="application/json")
        self.assertEqual(r.status_code, 403)


class MessagingPrivacyTests(TestCase):
    """Non-participants must never see or write to a conversation."""

    def setUp(self):
        self.a, self.b, self.eve = make_user("pa"), make_user("pb"), make_user("peve")
        self.convo = send_message(self.a, self.b, "Secret plan").conversation
        self.client.force_login(self.eve)

    def test_cannot_view_conversation(self):
        self.assertEqual(self.client.get(reverse("messaging:conversation", args=[self.convo.pk])).status_code, 404)

    def test_cannot_poll_messages(self):
        r = self.client.get(reverse("messaging:api_messages", args=[self.convo.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertNotIn(b"Secret", r.content)

    def test_cannot_send_messages(self):
        r = self.client.post(reverse("messaging:api_send", args=[self.convo.pk]), json.dumps({"body": "hi"}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Message.objects.count(), 1)

    def test_inbox_excludes_others(self):
        self.assertNotContains(self.client.get(reverse("messaging:inbox")), "Secret plan")
