from django.urls import path

from . import views

app_name = "mentorship"

urlpatterns = [
    path("", views.senior_list, name="list"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("incoming/", views.incoming_requests, name="incoming"),
    path("my-profile/", views.edit_senior_profile, name="edit_profile"),
    path("<int:pk>/", views.senior_detail, name="detail"),
    path("<int:pk>/request/", views.send_request, name="send_request"),
    path("requests/<int:pk>/<str:action>/", views.respond_request, name="respond"),
]
