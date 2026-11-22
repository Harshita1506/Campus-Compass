from django.conf import settings


def site_context(request):
    unread = 0
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
    return {
        "SITE_NAME": "Campus Compass",
        "SITE_TAGLINE": "Your College. Your Community. Your Guide.",
        "unread_notification_count": unread,
        "is_site_admin": request.user.is_authenticated and request.user.is_site_admin,
        "DEBUG": settings.DEBUG,
    }
