from django.urls import path

from . import views

app_name = "lostfound"

urlpatterns = [
    path("", views.item_list, name="list"),
    path("mine/", views.my_items, name="my_items"),
    path("new/", views.item_create, name="create"),
    path("<int:pk>/", views.item_detail, name="detail"),
    path("<int:pk>/edit/", views.item_edit, name="edit"),
    path("<int:pk>/delete/", views.item_delete, name="delete"),
    path("api/search/", views.api_search, name="api_search"),
    path("api/<int:pk>/status/", views.api_update_status, name="api_status"),
]
