from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.models import TimeStampedModel
from core.validators import validate_github_url, validate_linkedin_url


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SeniorProfile(TimeStampedModel):
    class Domain(models.TextChoices):
        SOFTWARE = "software", "Software Engineering"
        DATA = "data", "Data Science & AI"
        PRODUCT = "product", "Product Management"
        DESIGN = "design", "UI/UX Design"
        CORE = "core", "Core Engineering"
        FINANCE = "finance", "Finance & Consulting"
        RESEARCH = "research", "Research & Higher Studies"
        STARTUP = "startup", "Entrepreneurship"
        BLOCKCHAIN = "blockchain", "Blockchain & Web3"
        CYBER = "cyber", "Cybersecurity"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="senior_profile")
    branch = models.CharField(max_length=60)
    graduation_year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2040)],
                                                       db_index=True)
    current_company = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    domain = models.CharField(max_length=15, choices=Domain.choices, db_index=True)
    skills = models.ManyToManyField(Skill, related_name="seniors", blank=True)
    achievements = models.TextField(max_length=1500, blank=True)
    introduction = models.TextField(max_length=1500)
    linkedin_url = models.URLField(blank=True, validators=[validate_linkedin_url])
    github_url = models.URLField(blank=True, validators=[validate_github_url])
    mentorship_interests = models.CharField(max_length=255, help_text="e.g. Resume reviews, DSA, internships")
    is_available = models.BooleanField(default=True, help_text="Accepting new mentorship requests")

    class Meta:
        ordering = ["-graduation_year", "user__first_name"]

    def __str__(self):
        return f"{self.user.display_name} ({self.graduation_year})"

    def get_absolute_url(self):
        return reverse("mentorship:detail", args=[self.pk])


class MentorshipRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="mentorship_requests_sent")
    senior = models.ForeignKey(SeniorProfile, on_delete=models.CASCADE, related_name="requests")
    topic = models.CharField(max_length=120)
    message = models.TextField(max_length=1000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    response_note = models.TextField(max_length=500, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["student", "senior"], condition=Q(status="pending"),
                                               name="unique_pending_mentorship_request")]

    def __str__(self):
        return f"{self.student} → {self.senior} ({self.status})"
