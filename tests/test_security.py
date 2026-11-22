"""Cross-cutting security tests: authentication, CSRF, ownership, role restrictions."""
from django.test import Client, TestCase
from django.urls import reverse

from tests.helpers import make_item, make_product, make_user


class AuthenticationRequiredTests(TestCase):
    PROTECTED = ["dashboard:home", "lostfound:list", "marketplace:list", "roommates:list", "locator:map",
                 "mentorship:list", "announcements:list", "notifications:list", "messaging:inbox",
                 "marketplace:api_search", "locator:api_search", "notifications:api_unread"]

    def test_anonymous_redirected_to_login(self):
        for name in self.PROTECTED:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse("accounts:login"), response["Location"])


class CSRFTests(TestCase):
    def test_state_changing_ajax_requires_csrf(self):
        owner = make_user("csrfowner")
        product = make_product(owner)
        client = Client(enforce_csrf_checks=True)
        client.force_login(make_user("csrfbuyer"))
        self.assertEqual(client.post(reverse("marketplace:api_save", args=[product.pk])).status_code, 403)
        client.force_login(owner)
        self.assertEqual(client.post(reverse("marketplace:api_status", args=[product.pk]),
                                     {"status": "sold"}).status_code, 403)


class OwnershipTests(TestCase):
    def test_users_cannot_modify_others_listings(self):
        owner, attacker = make_user("victim"), make_user("attacker")
        product, item = make_product(owner), make_item(owner)
        self.client.force_login(attacker)
        self.client.post(reverse("marketplace:edit", args=[product.pk]), {
            "title": "HACKED", "category": "books", "condition": "good", "price": "1", "description": "x"})
        self.client.post(reverse("lostfound:edit", args=[item.pk]), {
            "item_type": "lost", "title": "HACKED", "category": "other", "description": "x", "location": "x",
            "date": "2024-01-01"})
        product.refresh_from_db()
        item.refresh_from_db()
        self.assertNotEqual(product.title, "HACKED")
        self.assertNotEqual(item.title, "HACKED")

    def test_get_not_allowed_on_ajax_mutations(self):
        owner = make_user("getowner")
        product = make_product(owner)
        self.client.force_login(owner)
        self.assertEqual(self.client.get(reverse("marketplace:api_status", args=[product.pk])).status_code, 405)


class XSSTests(TestCase):
    def test_user_content_is_escaped(self):
        owner = make_user("xss")
        make_product(owner, title="<script>alert(1)</script>")
        self.client.force_login(owner)
        r = self.client.get(reverse("marketplace:list"))
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertContains(r, "&lt;script&gt;")
