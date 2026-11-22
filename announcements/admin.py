from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "event_date", "is_pinned", "is_published", "created_at")
    list_filter = ("category", "is_pinned", "is_published")
    list_editable = ("is_pinned", "is_published")
    search_fields = ("title", "body")

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
