from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel
from core.validators import validate_safe_external_url


class Announcement(TimeStampedModel):
    class Category(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        EXAM = "exam", "Examinations"
        EVENT = "event", "Event"
        PLACEMENT = "placement", "Placements & Internships"
        CLUB = "club", "Clubs & Societies"
        HOSTEL = "hostel", "Hostel"
        SPORTS = "sports", "Sports"
        GENERAL = "general", "General"

    title = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.GENERAL, db_index=True)
    event_date = models.DateTimeField(null=True, blank=True, help_text="Leave empty for non-event announcements")
    venue = models.CharField(max_length=150, blank=True)
    registration_link = models.URLField(blank=True, validators=[validate_safe_external_url])
    is_pinned = models.BooleanField(default=False, db_index=True)
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("announcements:detail", args=[self.pk])

    @property
    def is_upcoming(self):
        return self.event_date is not None and self.event_date >= timezone.now()
