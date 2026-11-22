import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel
from core.utils import UploadTo
from core.validators import validate_image_file, validate_linkedin_url


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        SENIOR = "senior", "Senior / Alumni"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT, db_index=True)
    is_email_verified = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def is_site_admin(self):
        return self.is_staff or self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_senior(self):
        return self.role == self.Role.SENIOR

    @property
    def initials(self):
        name = self.display_name.split()
        return "".join(part[0] for part in name[:2]).upper() or "U"


class Profile(TimeStampedModel):
    class Branch(models.TextChoices):
        CSE = "CSE", "Computer Science & Engineering"
        ECE = "ECE", "Electronics & Communication"
        ME = "ME", "Mechanical Engineering"
        CE = "CE", "Civil Engineering"
        EEE = "EEE", "Electrical Engineering"
        BT = "BT", "Biotechnology"
        BBA = "BBA", "Business Administration"
        LAW = "LAW", "Law"
        DES = "DES", "Design"
        OTHER = "OTHER", "Other"

    class Year(models.IntegerChoices):
        FIRST = 1, "1st Year"
        SECOND = 2, "2nd Year"
        THIRD = 3, "3rd Year"
        FOURTH = 4, "4th Year"
        FIFTH = 5, "5th Year"
        ALUMNI = 6, "Alumni"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    branch = models.CharField(max_length=10, choices=Branch.choices, default=Branch.CSE)
    academic_year = models.PositiveSmallIntegerField(choices=Year.choices, default=Year.FIRST)
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to=UploadTo("avatars"), blank=True, validators=[validate_image_file])
    linkedin_url = models.URLField(blank=True, validators=[validate_linkedin_url])

    def __str__(self):
        return f"Profile of {self.user}"


class EmailOTP(models.Model):
    """One-time password for email verification. Only a hash of the code is stored."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_used"])]

    @classmethod
    def generate_for(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        code = f"{random.SystemRandom().randint(0, 999999):06d}"
        otp = cls.objects.create(user=user, code_hash=make_password(code))
        return otp, code

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    def verify(self, code):
        if self.is_used or self.is_expired or self.attempts >= settings.OTP_MAX_ATTEMPTS:
            return False
        self.attempts += 1
        ok = check_password(code, self.code_hash)
        if ok:
            self.is_used = True
        self.save(update_fields=["attempts", "is_used"])
        return ok
