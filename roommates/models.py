from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.models import TimeStampedModel


class RoommateProfile(TimeStampedModel):
    class Location(models.TextChoices):
        ON_CAMPUS = "on_campus", "On-campus hostel"
        NORTH_GATE = "north_gate", "North Gate area"
        SOUTH_GATE = "south_gate", "South Gate area"
        CITY_CENTRE = "city_centre", "City centre"
        METRO = "metro", "Near metro station"
        ANY = "any", "Anywhere nearby"

    class Accommodation(models.TextChoices):
        HOSTEL = "hostel", "College hostel"
        PG = "pg", "PG / Paying guest"
        FLAT = "flat", "Shared flat"
        STUDIO = "studio", "Studio (2 sharing)"

    class Food(models.TextChoices):
        VEG = "veg", "Vegetarian"
        VEGAN = "vegan", "Vegan"
        EGG = "egg", "Eggetarian"
        NONVEG = "nonveg", "Non-vegetarian"
        ANY = "any", "No preference"

    class Sleep(models.TextChoices):
        EARLY = "early", "Early bird (sleep before 11 pm)"
        NIGHT = "night", "Night owl (sleep after 1 am)"
        FLEXIBLE = "flexible", "Flexible"

    class Cleanliness(models.IntegerChoices):
        VERY_TIDY = 3, "Very tidy"
        MODERATE = 2, "Moderately tidy"
        RELAXED = 1, "Relaxed"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roommate_profile")
    headline = models.CharField(max_length=120, help_text="e.g. 2nd-year CSE looking for a calm flatmate")
    about = models.TextField(max_length=1000, blank=True)
    budget_min = models.PositiveIntegerField(validators=[MinValueValidator(0)], help_text="Monthly, in ₹")
    budget_max = models.PositiveIntegerField(validators=[MinValueValidator(0)], help_text="Monthly, in ₹")
    preferred_location = models.CharField(max_length=20, choices=Location.choices, db_index=True)
    accommodation_type = models.CharField(max_length=10, choices=Accommodation.choices, db_index=True)
    food_preference = models.CharField(max_length=10, choices=Food.choices)
    sleep_schedule = models.CharField(max_length=10, choices=Sleep.choices)
    cleanliness = models.PositiveSmallIntegerField(choices=Cleanliness.choices, default=Cleanliness.MODERATE)
    move_in_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="saved_roommates", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.display_name} — {self.headline}"

    def clean(self):
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValidationError({"budget_max": "Maximum budget must be greater than minimum budget."})

    def get_absolute_url(self):
        return reverse("roommates:detail", args=[self.pk])


class RoommateRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roommate_requests_sent")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="roommate_requests_received")
    message = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], condition=Q(status="pending"),
                                    name="unique_pending_roommate_request"),
            models.CheckConstraint(condition=~Q(sender=models.F("receiver")), name="roommate_request_not_self"),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"
