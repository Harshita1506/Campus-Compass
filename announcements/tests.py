from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from announcements.models import Announcement
from notifications.models import Notification
from tests.helpers import make_admin, make_user


class AnnouncementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.student = make_user("reader")

    def test_admin_crud(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("announcements:create"), {
            "title": "Fest", "category": "event", "body": "Join us", "event_date": "2030-01-10T10:00",
            "venue": "Hall", "registration_link": "https://example.com/r", "is_pinned": "on", "is_published": "on",
            "notify_students": "on"})
        ann = Announcement.objects.get(title="Fest")
        self.assertTrue(ann.is_pinned)
        self.assertTrue(Notification.objects.filter(recipient=self.student, notification_type="announcement").exists())
        self.client.post(reverse("announcements:edit", args=[ann.pk]), {
            "title": "Fest 2", "category": "event", "body": "Join", "is_published": "on"})
        ann.refresh_from_db()
        self.assertEqual(ann.title, "Fest 2")
        self.client.post(reverse("announcements:toggle_pin", args=[ann.pk]))
        ann.refresh_from_db()
        self.assertTrue(ann.is_pinned)
        self.client.post(reverse("announcements:delete", args=[ann.pk]))
        self.assertFalse(Announcement.objects.exists())

    def test_student_cannot_manage(self):
        self.client.force_login(self.student)
        for url in [reverse("announcements:manage"), reverse("announcements:create")]:
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_unsafe_registration_link_rejected(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("announcements:create"), {
            "title": "Bad", "category": "general", "body": "x", "registration_link": "javascript:alert(1)",
            "is_published": "on"})
        self.assertFalse(Announcement.objects.filter(title="Bad").exists())

    def test_student_filters(self):
        Announcement.objects.create(title="Exam timetable", body="b", category="exam")
        Announcement.objects.create(title="Upcoming fest", body="b", category="event",
                                    event_date=timezone.now() + timedelta(days=3))
        Announcement.objects.create(title="Draft", body="b", is_published=False)
        self.client.force_login(self.student)
        r = self.client.get(reverse("announcements:list"), {"category": "exam"})
        self.assertContains(r, "Exam timetable")
        self.assertNotContains(r, "Upcoming fest")
        r = self.client.get(reverse("announcements:list"), {"upcoming": "true"})
        self.assertContains(r, "Upcoming fest")
        self.assertNotContains(r, "Draft")
