from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("sell/", views.product_create, name="create"),
    path("mine/", views.my_listings, name="my_listings"),
    path("saved/", views.saved_products, name="saved"),
    path("seller/<str:username>/", views.seller_profile, name="seller"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("<int:pk>/edit/", views.product_edit, name="edit"),
    path("<int:pk>/delete/", views.product_delete, name="delete"),
    path("<int:pk>/enquire/", views.enquire, name="enquire"),
    path("<int:pk>/report/", views.report, name="report"),
    path("api/search/", views.api_search, name="api_search"),
    path("api/<int:pk>/save/", views.api_toggle_save, name="api_save"),
    path("api/<int:pk>/status/", views.api_update_status, name="api_status"),
]
