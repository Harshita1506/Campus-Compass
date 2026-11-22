from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel
from core.utils import UploadTo
from core.validators import validate_image_file


class Product(TimeStampedModel):
    class Category(models.TextChoices):
        BOOKS = "books", "Books & Notes"
        ELECTRONICS = "electronics", "Electronics"
        FURNITURE = "furniture", "Furniture"
        CYCLES = "cycles", "Cycles & Vehicles"
        CLOTHING = "clothing", "Clothing"
        STATIONERY = "stationery", "Stationery & Lab"
        SPORTS = "sports", "Sports & Fitness"
        HOSTEL = "hostel", "Hostel Essentials"
        OTHER = "other", "Other"

    class Condition(models.TextChoices):
        NEW = "new", "Brand new"
        LIKE_NEW = "like_new", "Like new"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=2000)
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.GOOD)
    image = models.ImageField(upload_to=UploadTo("products"), blank=True, validators=[validate_image_file])
    image_2 = models.ImageField(upload_to=UploadTo("products"), blank=True, validators=[validate_image_file])
    image_3 = models.ImageField(upload_to=UploadTo("products"), blank=True, validators=[validate_image_file])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE, db_index=True)
    is_hidden = models.BooleanField(default=False, help_text="Hidden by a moderator")
    sold_at = models.DateTimeField(null=True, blank=True)
    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, through="SavedProduct", related_name="saved_products",
                                      blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "category"]), models.Index(fields=["price"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("marketplace:detail", args=[self.pk])

    @property
    def images(self):
        return [img for img in (self.image, self.image_2, self.image_3) if img]


class SavedProduct(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_saved_product")]


class Enquiry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="enquiries")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enquiries")
    message = models.TextField(max_length=1000)
    offered_price = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "enquiries"

    def __str__(self):
        return f"Enquiry by {self.buyer} on {self.product}"


class ProductReport(models.Model):
    class Reason(models.TextChoices):
        SCAM = "scam", "Suspected scam / fraud"
        PROHIBITED = "prohibited", "Prohibited item"
        MISLEADING = "misleading", "Misleading information"
        DUPLICATE = "duplicate", "Duplicate listing"
        OFFENSIVE = "offensive", "Offensive content"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACTION_TAKEN = "action_taken", "Action taken"
        DISMISSED = "dismissed", "Dismissed"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_reports")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "reporter"], name="unique_report_per_user")]

    def __str__(self):
        return f"Report on {self.product} ({self.get_reason_display()})"
