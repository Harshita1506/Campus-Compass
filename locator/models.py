from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel


class Building(TimeStampedModel):
    class Type(models.TextChoices):
        ACADEMIC = "academic", "Academic block"
        LAB = "lab", "Laboratory block"
        LIBRARY = "library", "Library"
        CAFETERIA = "cafeteria", "Cafeteria / Food court"
        ADMIN = "admin", "Administration"
        HOSTEL = "hostel", "Hostel"
        SPORTS = "sports", "Sports complex"
        AUDITORIUM = "auditorium", "Auditorium"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Short code, e.g. A-BLK")
    building_type = models.CharField(max_length=15, choices=Type.choices, default=Type.ACADEMIC, db_index=True)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,
                                   validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6,
                                    validators=[MinValueValidator(-180), MaxValueValidator(180)])
    floors = models.PositiveSmallIntegerField(default=1)
    opening_hours = models.CharField(max_length=80, blank=True)
    is_demo = models.BooleanField(default=True, help_text="Fictional demo data — replace with your campus data")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=10, unique=True)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="departments")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(TimeStampedModel):
    class Type(models.TextChoices):
        CLASSROOM = "classroom", "Classroom"
        LAB = "lab", "Laboratory"
        FACULTY_CABIN = "cabin", "Faculty cabin"
        OFFICE = "office", "Office"
        SEMINAR = "seminar", "Seminar hall"
        LIBRARY = "library", "Library section"
        CAFETERIA = "cafeteria", "Cafeteria"
        OTHER = "other", "Other"

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    name = models.CharField(max_length=120, blank=True, help_text="e.g. AI & ML Lab")
    room_type = models.CharField(max_length=15, choices=Type.choices, default=Type.CLASSROOM, db_index=True)
    floor = models.SmallIntegerField(default=0, help_text="0 = ground floor")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="rooms")
    faculty_name = models.CharField(max_length=120, blank=True, help_text="For faculty cabins")
    capacity = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["building__name", "floor", "room_number"]
        constraints = [models.UniqueConstraint(fields=["building", "room_number"], name="unique_room_in_building")]
        indexes = [models.Index(fields=["room_number"])]

    def __str__(self):
        return f"{self.building.code}-{self.room_number} {self.name}".strip()

    @property
    def floor_label(self):
        if self.floor == 0:
            return "Ground floor"
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(self.floor if self.floor < 20 else self.floor % 10, "th")
        return f"{self.floor}{suffix} floor"
