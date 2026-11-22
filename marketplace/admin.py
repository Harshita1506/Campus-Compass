from django.contrib import admin

from .models import Enquiry, Product, ProductReport, SavedProduct


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "category", "price", "condition", "status", "is_hidden", "created_at")
    list_filter = ("category", "status", "condition", "is_hidden")
    search_fields = ("title", "description", "seller__username")
    list_editable = ("status", "is_hidden")


@admin.register(ProductReport)
class ProductReportAdmin(admin.ModelAdmin):
    list_display = ("product", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason")


admin.site.register(Enquiry)
admin.site.register(SavedProduct)
