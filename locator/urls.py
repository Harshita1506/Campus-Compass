from django.urls import path

from . import views

app_name = "locator"

urlpatterns = [
    path("", views.map_view, name="map"),
    path("api/buildings/", views.api_buildings, name="api_buildings"),
    path("api/search/", views.api_search, name="api_search"),
]
