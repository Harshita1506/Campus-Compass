from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views as core_views

admin.site.site_header = "Campus Compass Administration"
admin.site.site_title = "Campus Compass Admin"
admin.site.index_title = "Data management"

urlpatterns = [
    path("", core_views.landing, name="landing"),
    path("django-admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("lost-found/", include("lostfound.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("roommates/", include("roommates.urls")),
    path("locator/", include("locator.urls")),
    path("mentorship/", include("mentorship.urls")),
    path("announcements/", include("announcements.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("messaging.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
