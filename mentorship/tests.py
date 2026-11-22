from django.test import TestCase
from django.urls import reverse

from mentorship.models import MentorshipRequest, SeniorProfile, Skill
from notifications.models import Notification
from tests.helpers import make_user


class MentorshipTests(TestCase):
    def setUp(self):
        self.senior_user = make_user("senior1", role="senior")
        self.student = make_user("junior1")
        self.senior = SeniorProfile.objects.create(user=self.senior_user, branch="CSE", graduation_year=2023,
                                                   domain="software", introduction="Hi", mentorship_interests="DSA",
                                                   current_company="Example Co")
        self.senior.skills.add(Skill.objects.create(name="Python"))

    def test_browse_and_filter(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse("mentorship:list"), {"skill": "python"}), "Senior1")
        self.assertNotContains(self.client.get(reverse("mentorship:list"), {"domain": "design"}), "Senior1")
        self.assertContains(self.client.get(reverse("mentorship:list"), {"graduation_year": 2023}), "Senior1")

    def test_request_accept_flow(self):
        self.client.force_login(self.student)
        self.client.post(reverse("mentorship:send_request", args=[self.senior.pk]),
                         {"topic": "Internships", "message": "Please guide me"})
        req = MentorshipRequest.objects.get()
        self.assertEqual(req.status, "pending")
        self.assertTrue(Notification.objects.filter(recipient=self.senior_user,
                                                    notification_type="mentorship_request").exists())
        # student cannot respond to own request
        self.assertEqual(self.client.post(reverse("mentorship:respond", args=[req.pk, "accept"])).status_code, 403)
        self.client.force_login(self.senior_user)
        self.client.post(reverse("mentorship:respond", args=[req.pk, "accept"]), {"response_note": "Sure"})
        req.refresh_from_db()
        self.assertEqual(req.status, "accepted")
        self.assertEqual(req.response_note, "Sure")
        self.assertTrue(Notification.objects.filter(recipient=self.student, notification_type="request_accepted").exists())

    def test_reject(self):
        req = MentorshipRequest.objects.create(student=self.student, senior=self.senior, topic="t", message="m")
        self.client.force_login(self.senior_user)
        self.client.post(reverse("mentorship:respond", args=[req.pk, "reject"]))
        req.refresh_from_db()
        self.assertEqual(req.status, "rejected")

    def test_no_duplicate_pending_and_unavailable(self):
        self.client.force_login(self.student)
        url = reverse("mentorship:send_request", args=[self.senior.pk])
        self.client.post(url, {"topic": "a", "message": "b"})
        self.client.post(url, {"topic": "a", "message": "b"})
        self.assertEqual(MentorshipRequest.objects.count(), 1)
        self.senior.is_available = False
        self.senior.save()
        MentorshipRequest.objects.all().delete()
        self.client.post(url, {"topic": "a", "message": "b"})
        self.assertEqual(MentorshipRequest.objects.count(), 0)

    def test_only_seniors_access_incoming_and_profile_form(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("mentorship:incoming")).status_code, 403)
        self.assertEqual(self.client.get(reverse("mentorship:edit_profile")).status_code, 403)

    def test_senior_profile_form_saves_skills(self):
        self.client.force_login(self.senior_user)
        self.client.post(reverse("mentorship:edit_profile"), {
            "branch": "CSE", "graduation_year": 2023, "current_company": "X", "designation": "SDE",
            "domain": "software", "skills_text": "Django, React, django", "introduction": "Hello",
            "achievements": "", "mentorship_interests": "Interviews",
            "linkedin_url": "https://www.linkedin.com/in/senior-one", "github_url": "", "is_available": "on"})
        self.senior.refresh_from_db()
        self.assertEqual(sorted(self.senior.skills.values_list("name", flat=True)), ["Django", "React"])

    def test_unsafe_linkedin_rejected(self):
        self.client.force_login(self.senior_user)
        self.client.post(reverse("mentorship:edit_profile"), {
            "branch": "CSE", "graduation_year": 2023, "domain": "software", "skills_text": "Go",
            "introduction": "Hello", "mentorship_interests": "x", "linkedin_url": "javascript:alert(1)"})
        self.senior.refresh_from_db()
        self.assertEqual(self.senior.linkedin_url, "")
