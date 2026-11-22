from django.urls import path

from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.announcement_list, name="list"),
    path("manage/", views.manage, name="manage"),
    path("manage/new/", views.announcement_create, name="create"),
    path("manage/<int:pk>/edit/", views.announcement_edit, name="edit"),
    path("manage/<int:pk>/delete/", views.announcement_delete, name="delete"),
    path("manage/<int:pk>/pin/", views.toggle_pin, name="toggle_pin"),
    path("<int:pk>/", views.announcement_detail, name="detail"),
]
