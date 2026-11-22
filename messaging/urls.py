from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("<int:pk>/", views.conversation, name="conversation"),
    path("<int:pk>/send/", views.send_fallback, name="send"),
    path("start/<int:user_id>/", views.start_conversation, name="start"),
    path("api/<int:pk>/messages/", views.api_messages, name="api_messages"),
    path("api/<int:pk>/send/", views.api_send, name="api_send"),
    path("api/unread/", views.api_unread_count, name="api_unread"),
]
