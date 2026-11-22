from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.validators import (validate_github_url, validate_image_file,
                             validate_linkedin_url, validate_safe_external_url)


class ValidatorTests(SimpleTestCase):
    def test_linkedin_validator(self):
        validate_linkedin_url("https://www.linkedin.com/in/demo-user")
        with self.assertRaises(ValidationError):
            validate_linkedin_url("https://evil.com/linkedin.com")
        with self.assertRaises(ValidationError):
            validate_linkedin_url("http://linkedin.com/in/x")

    def test_github_validator(self):
        validate_github_url("https://github.com/demo")
        with self.assertRaises(ValidationError):
            validate_github_url("https://gitlab.com/demo")

    def test_safe_url_blocks_javascript(self):
        with self.assertRaises(ValidationError):
            validate_safe_external_url("javascript:alert(1)")
        validate_safe_external_url("https://forms.example.com/register")

    def test_image_extension_rejected(self):
        bad = SimpleUploadedFile("shell.php", b"<?php ?>", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_image_file(bad)


class LandingPageTests(TestCase):
    def test_landing_renders(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campus Compass")
