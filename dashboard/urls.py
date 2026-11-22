from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", views.admin_index, name="admin"),
    path("admin/api/stats/", views.admin_stats_api, name="admin_stats_api"),
    path("admin/export/<str:report>/", views.export_csv, name="export_csv"),
    path("admin/moderation/", views.moderation, name="moderation"),
    path("admin/moderation/report/<int:pk>/<str:action>/", views.moderate_report, name="moderate_report"),
    path("admin/moderation/product/<int:pk>/toggle/", views.toggle_product_visibility, name="toggle_product"),
    path("admin/moderation/item/<int:pk>/delete/", views.delete_item, name="delete_item"),
    path("admin/students/", views.students, name="students"),
    path("admin/students/<int:pk>/<str:action>/", views.student_action, name="student_action"),
    path("admin/locations/", views.buildings, name="buildings"),
    path("admin/locations/building/new/", views.building_form, name="building_create"),
    path("admin/locations/building/<int:pk>/", views.building_form, name="building_edit"),
    path("admin/locations/room/new/", views.room_form, name="room_create"),
    path("admin/locations/room/<int:pk>/", views.room_form, name="room_edit"),
    path("admin/locations/department/new/", views.department_form, name="department_create"),
    path("admin/locations/department/<int:pk>/", views.department_form, name="department_edit"),
    path("admin/locations/<str:kind>/<int:pk>/delete/", views.delete_location, name="delete_location"),
    path("admin/enquiries/", views.enquiries, name="enquiries"),
]
