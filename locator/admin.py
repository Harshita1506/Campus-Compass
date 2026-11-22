from django.contrib import admin

from .models import Building, Department, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "building_type", "floors", "latitude", "longitude", "is_demo")
    list_filter = ("building_type", "is_demo")
    search_fields = ("name", "code")
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "name", "building", "floor", "room_type", "department", "faculty_name")
    list_filter = ("room_type", "building", "floor")
    search_fields = ("room_number", "name", "faculty_name")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "building")
