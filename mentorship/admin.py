from django.contrib import admin

from .models import MentorshipRequest, SeniorProfile, Skill


@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "graduation_year", "current_company", "domain", "is_available")
    list_filter = ("domain", "graduation_year", "is_available")
    search_fields = ("user__first_name", "user__last_name", "current_company")
    filter_horizontal = ("skills",)


@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "senior", "topic", "status", "created_at")
    list_filter = ("status",)


admin.site.register(Skill)
