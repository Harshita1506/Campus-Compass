from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import EmailOTP
from tests.helpers import PASSWORD, make_user

User = get_user_model()


class RegistrationTests(TestCase):
    def _payload(self, **kw):
        data = {"first_name": "Test", "last_name": "Student", "username": "tstudent", "email": "t@example.test",
                "role": "student", "branch": "CSE", "academic_year": 2, "password1": PASSWORD, "password2": PASSWORD}
        data.update(kw)
        return data

    def test_register_creates_user_and_sends_otp(self):
        response = self.client.post(reverse("accounts:register"), self._payload())
        self.assertRedirects(response, reverse("accounts:verify_otp"))
        user = User.objects.get(username="tstudent")
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.check_password(PASSWORD))  # stored hashed
        self.assertNotEqual(user.password, PASSWORD)
        self.assertEqual(user.profile.branch, "CSE")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verification code", mail.outbox[0].body)

    def test_weak_password_rejected(self):
        response = self.client.post(reverse("accounts:register"), self._payload(password1="12345678",
                                                                                 password2="12345678"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="tstudent").exists())

    def test_duplicate_email_rejected(self):
        make_user("existing")
        response = self.client.post(reverse("accounts:register"), self._payload(email="existing@example.test"))
        self.assertContains(response, "already exists")

    def test_cannot_self_register_as_admin(self):
        self.client.post(reverse("accounts:register"), self._payload(role="admin"))
        self.assertFalse(User.objects.filter(username="tstudent").exists())


class OTPTests(TestCase):
    def setUp(self):
        self.user = make_user("otpuser", verified=False)
        self.client.force_login(self.user)

    def test_unverified_user_redirected_to_verify(self):
        response = self.client.get(reverse("marketplace:list"))
        self.assertRedirects(response, reverse("accounts:verify_otp"))

    def test_correct_otp_verifies(self):
        _, code = EmailOTP.generate_for(self.user)
        response = self.client.post(reverse("accounts:verify_otp"), {"code": code})
        self.assertRedirects(response, reverse("dashboard:home"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_wrong_otp_fails_and_locks_after_attempts(self):
        _, code = EmailOTP.generate_for(self.user)
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(5):
            self.client.post(reverse("accounts:verify_otp"), {"code": wrong})
        response = self.client.post(reverse("accounts:verify_otp"), {"code": code})
        self.assertEqual(response.status_code, 200)  # locked even with correct code
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_otp_stored_hashed(self):
        otp, code = EmailOTP.generate_for(self.user)
        self.assertNotEqual(otp.code_hash, code)


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_user("loginuser")

    def test_login_with_username(self):
        response = self.client.post(reverse("accounts:login"), {"username": "loginuser", "password": PASSWORD})
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_login_with_email(self):
        response = self.client.post(reverse("accounts:login"),
                                    {"username": "loginuser@example.test", "password": PASSWORD})
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_bad_password(self):
        response = self.client.post(reverse("accounts:login"), {"username": "loginuser", "password": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileTests(TestCase):
    def test_edit_profile_validates_linkedin(self):
        user = make_user("profileuser")
        self.client.force_login(user)
        data = {"first_name": "P", "last_name": "U", "branch": "ECE", "academic_year": 3, "phone": "",
                "linkedin_url": "https://evil.example.com/x", "bio": ""}
        response = self.client.post(reverse("accounts:edit_profile"), data)
        self.assertEqual(response.status_code, 200)
        data["linkedin_url"] = "https://www.linkedin.com/in/profile-user"
        response = self.client.post(reverse("accounts:edit_profile"), data)
        self.assertRedirects(response, reverse("accounts:profile"))
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.branch, "ECE")
