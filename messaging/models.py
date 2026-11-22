from django.conf import settings
from django.db import models


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(participants=user)


class Conversation(models.Model):
    """A private one-to-one conversation between exactly two users."""

    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    participant_key = models.CharField(max_length=50, unique=True, help_text="'<min_id>-<max_id>'")
    subject = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = ConversationQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation {self.participant_key}"

    @staticmethod
    def key_for(user_a, user_b):
        a, b = sorted([user_a.pk, user_b.pk])
        return f"{a}-{b}"

    @classmethod
    def get_or_create_between(cls, user_a, user_b, subject=""):
        convo, created = cls.objects.get_or_create(participant_key=cls.key_for(user_a, user_b),
                                                   defaults={"subject": subject[:150]})
        if created:
            convo.participants.add(user_a, user_b)
        return convo, created

    def other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def has_participant(self, user):
        return self.participants.filter(pk=user.pk).exists()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"
