from django.urls import reverse

from notifications.models import Notification
from notifications.utils import notify

from .models import Conversation, Message


def send_message(sender, recipient, body, subject=""):
    convo, _ = Conversation.get_or_create_between(sender, recipient, subject=subject)
    msg = Message.objects.create(conversation=convo, sender=sender, body=body.strip()[:2000])
    convo.save(update_fields=["updated_at"])
    url = reverse("messaging:conversation", args=[convo.pk])
    # Avoid flooding: refresh an existing unread message notification from the same sender
    existing = Notification.objects.filter(recipient=recipient, actor=sender, is_read=False,
                                           notification_type=Notification.Type.MESSAGE).first()
    if existing:
        existing.message = msg.body[:300]
        existing.save(update_fields=["message"])
    else:
        notify(recipient, Notification.Type.MESSAGE, f"New message from {sender.display_name}", msg.body, url, sender)
    return msg
