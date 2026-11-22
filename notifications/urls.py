from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("<int:pk>/open/", views.open_notification, name="open"),
    path("api/unread/", views.api_unread, name="api_unread"),
    path("api/<int:pk>/read/", views.api_mark_read, name="api_mark_read"),
    path("api/read-all/", views.api_mark_all_read, name="api_mark_all_read"),
]
