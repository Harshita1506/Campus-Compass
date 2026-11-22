from django.urls import path

from . import views

app_name = "roommates"

urlpatterns = [
    path("", views.profile_list, name="list"),
    path("my-profile/", views.my_profile_edit, name="my_profile"),
    path("requests/", views.requests_view, name="requests"),
    path("saved/", views.saved_profiles, name="saved"),
    path("<int:pk>/", views.profile_detail, name="detail"),
    path("<int:pk>/request/", views.send_request, name="send_request"),
    path("requests/<int:pk>/<str:action>/", views.respond_request, name="respond"),
    path("api/filter/", views.api_filter, name="api_filter"),
    path("api/<int:pk>/save/", views.api_toggle_save, name="api_save"),
]
