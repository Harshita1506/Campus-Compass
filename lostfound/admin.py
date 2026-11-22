from django.contrib import admin

from .models import Item, ItemMatch


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "item_type", "category", "location", "date", "status", "owner", "created_at")
    list_filter = ("item_type", "status", "category")
    search_fields = ("title", "description", "location", "owner__username")
    date_hierarchy = "created_at"


@admin.register(ItemMatch)
class ItemMatchAdmin(admin.ModelAdmin):
    list_display = ("lost_item", "found_item", "score", "created_at")
