from django.contrib import admin

from .models import RoommateProfile, RoommateRequest


@admin.register(RoommateProfile)
class RoommateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "budget_min", "budget_max", "preferred_location", "accommodation_type",
                    "is_active")
    list_filter = ("preferred_location", "accommodation_type", "food_preference", "sleep_schedule", "is_active")
    search_fields = ("headline", "user__username")


@admin.register(RoommateRequest)
class RoommateRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at")
    list_filter = ("status",)
