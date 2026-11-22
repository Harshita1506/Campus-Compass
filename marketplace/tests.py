from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from marketplace.models import Enquiry, Product, ProductReport, SavedProduct
from messaging.models import Conversation
from notifications.models import Notification
from tests.helpers import make_product, make_user

# 1x1 transparent GIF
TINY_GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")


class ProductCrudTests(TestCase):
    def setUp(self):
        self.seller = make_user("seller")
        self.buyer = make_user("buyer")

    def test_create_product_with_image(self):
        self.client.force_login(self.seller)
        image = SimpleUploadedFile("pic.gif", TINY_GIF, content_type="image/gif")
        response = self.client.post(reverse("marketplace:create"), {
            "title": "Desk lamp", "category": "hostel", "condition": "good", "price": "250",
            "description": "Works great", "image": image})
        product = Product.objects.get(title="Desk lamp")
        self.assertRedirects(response, product.get_absolute_url())
        self.assertTrue(product.image.name.startswith("products/"))
        self.assertNotIn("pic", product.image.name)  # random filename
        product.image.delete()

    def test_fake_image_rejected(self):
        self.client.force_login(self.seller)
        fake = SimpleUploadedFile("evil.png", b"not really an image", content_type="image/png")
        self.client.post(reverse("marketplace:create"), {
            "title": "Bad", "category": "other", "condition": "good", "price": "1", "description": "x", "image": fake})
        self.assertFalse(Product.objects.filter(title="Bad").exists())

    def test_negative_price_rejected(self):
        self.client.force_login(self.seller)
        self.client.post(reverse("marketplace:create"), {
            "title": "Neg", "category": "other", "condition": "good", "price": "-5", "description": "x"})
        self.assertFalse(Product.objects.filter(title="Neg").exists())

    def test_non_owner_cannot_edit_delete_or_change_status(self):
        product = make_product(self.seller)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("marketplace:edit", args=[product.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("marketplace:delete", args=[product.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("marketplace:api_status", args=[product.pk]),
                                          {"status": "sold"}).status_code, 403)
        product.refresh_from_db()
        self.assertEqual(product.status, "available")

    def test_owner_marks_sold(self):
        product = make_product(self.seller)
        self.client.force_login(self.seller)
        data = self.client.post(reverse("marketplace:api_status", args=[product.pk]), {"status": "sold"}).json()
        self.assertTrue(data["ok"])
        product.refresh_from_db()
        self.assertEqual(product.status, "sold")
        self.assertIsNotNone(product.sold_at)

    def test_owner_edit(self):
        product = make_product(self.seller)
        self.client.force_login(self.seller)
        self.client.post(reverse("marketplace:edit", args=[product.pk]), {
            "title": "Updated", "category": "books", "condition": "fair", "price": "200", "description": "x"})
        product.refresh_from_db()
        self.assertEqual(product.title, "Updated")


class MarketplaceSearchTests(TestCase):
    def setUp(self):
        self.user = make_user("shopper")
        seller = make_user("vendor")
        make_product(seller, title="Casio calculator", category="electronics", price=Decimal("700"))
        make_product(seller, title="Maths textbook", category="books", price=Decimal("300"))
        make_product(seller, title="Old cycle", category="cycles", price=Decimal("4000"), status="sold")
        make_product(seller, title="Hidden thing", category="books", price=Decimal("10"), is_hidden=True)
        self.client.force_login(self.user)

    def search(self, **params):
        return self.client.get(reverse("marketplace:api_search"), params).json()

    def test_text_search(self):
        self.assertEqual([r["title"] for r in self.search(q="calc")["results"]], ["Casio calculator"])

    def test_category_filter(self):
        self.assertEqual(self.search(category="books")["count"], 1)  # hidden excluded

    def test_price_range_and_sort(self):
        data = self.search(min_price=100, max_price=1000, sort="price_desc")
        self.assertEqual([r["title"] for r in data["results"]], ["Casio calculator", "Maths textbook"])

    def test_sold_excluded_by_default(self):
        self.assertEqual(self.search(q="cycle")["count"], 0)
        self.assertEqual(self.search(q="cycle", include_sold="on")["count"], 1)


class MarketplaceInteractionTests(TestCase):
    def setUp(self):
        self.seller, self.buyer = make_user("seller2"), make_user("buyer2")
        self.product = make_product(self.seller)
        self.client.force_login(self.buyer)

    def test_toggle_save(self):
        url = reverse("marketplace:api_save", args=[self.product.pk])
        self.assertTrue(self.client.post(url).json()["saved"])
        self.assertTrue(SavedProduct.objects.filter(user=self.buyer).exists())
        self.assertFalse(self.client.post(url).json()["saved"])
        self.assertFalse(SavedProduct.objects.filter(user=self.buyer).exists())

    def test_save_requires_post(self):
        self.assertEqual(self.client.get(reverse("marketplace:api_save", args=[self.product.pk])).status_code, 405)

    def test_enquiry_creates_notification_and_conversation(self):
        response = self.client.post(reverse("marketplace:enquire", args=[self.product.pk]),
                                    {"message": "Still available?", "offered_price": "250"})
        self.assertEqual(Enquiry.objects.count(), 1)
        convo = Conversation.objects.get()
        self.assertRedirects(response, reverse("messaging:conversation", args=[convo.pk]))
        self.assertTrue(Notification.objects.filter(recipient=self.seller, notification_type="enquiry").exists())

    def test_report_once_per_user(self):
        url = reverse("marketplace:report", args=[self.product.pk])
        self.client.post(url, {"reason": "scam", "details": "suspicious"})
        self.client.post(url, {"reason": "scam", "details": "again"})
        self.assertEqual(ProductReport.objects.count(), 1)

    def test_hidden_product_not_viewable_by_others(self):
        self.product.is_hidden = True
        self.product.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 403)

    def test_seller_profile_page(self):
        response = self.client.get(reverse("marketplace:seller", args=[self.seller.username]))
        self.assertContains(response, self.product.title)
