from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ENQUIRY = "enquiry", "Marketplace enquiry"
        ROOMMATE_REQUEST = "roommate_request", "Roommate request"
        MENTORSHIP_REQUEST = "mentorship_request", "Mentorship request"
        REQUEST_ACCEPTED = "request_accepted", "Request accepted"
        REQUEST_REJECTED = "request_rejected", "Request rejected"
        MESSAGE = "message", "New message"
        LOSTFOUND_MATCH = "lostfound_match", "Lost & found match"
        ANNOUNCEMENT = "announcement", "Announcement"
        MODERATION = "moderation", "Moderation"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="+")
    notification_type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"{self.title} → {self.recipient}"

    @property
    def icon(self):
        return {
            "enquiry": "bi-bag-heart", "roommate_request": "bi-house-heart", "mentorship_request": "bi-mortarboard",
            "request_accepted": "bi-check-circle", "request_rejected": "bi-x-circle", "message": "bi-chat-dots",
            "lostfound_match": "bi-search-heart", "announcement": "bi-megaphone", "moderation": "bi-shield-check",
        }.get(self.notification_type, "bi-bell")
