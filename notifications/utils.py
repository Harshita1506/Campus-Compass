from .models import Notification


def notify(recipient, notification_type, title, message="", url="", actor=None):
    """Create a notification. Never notifies a user about their own action."""
    if recipient is None or (actor is not None and actor.pk == recipient.pk):
        return None
    return Notification.objects.create(
        recipient=recipient, actor=actor, notification_type=notification_type,
        title=title[:150], message=message[:300], url=url[:300],
    )
