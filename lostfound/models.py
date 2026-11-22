from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel
from core.utils import UploadTo
from core.validators import validate_image_file


class Item(TimeStampedModel):
    class ItemType(models.TextChoices):
        LOST = "lost", "Lost"
        FOUND = "found", "Found"

    class Category(models.TextChoices):
        ELECTRONICS = "electronics", "Electronics"
        ID_CARD = "id_card", "ID / Cards"
        BOOKS = "books", "Books & Notes"
        BAGS = "bags", "Bags & Wallets"
        KEYS = "keys", "Keys"
        CLOTHING = "clothing", "Clothing"
        ACCESSORIES = "accessories", "Accessories & Jewellery"
        BOTTLES = "bottles", "Bottles & Lunchboxes"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RECOVERED = "recovered", "Recovered"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lostfound_items")
    item_type = models.CharField(max_length=5, choices=ItemType.choices, db_index=True)
    title = models.CharField("Item name", max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    description = models.TextField(max_length=1500)
    location = models.CharField(max_length=120, help_text="Where it was lost / found, e.g. Library 2nd floor")
    date = models.DateField(help_text="Date lost or found")
    image = models.ImageField(upload_to=UploadTo("lostfound"), blank=True, validators=[validate_image_file])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    recovered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["item_type", "status", "category"])]

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.title}"

    def get_absolute_url(self):
        return reverse("lostfound:detail", args=[self.pk])


class ItemMatch(models.Model):
    """A potential match between a lost item and a found item."""

    lost_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="matches_as_lost")
    found_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="matches_as_found")
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score"]
        constraints = [models.UniqueConstraint(fields=["lost_item", "found_item"], name="unique_item_match")]

    def __str__(self):
        return f"{self.lost_item} ↔ {self.found_item} ({self.score}%)"
