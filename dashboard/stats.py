"""Aggregate statistics for the admin dashboard. All numbers come from the database."""
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate

from announcements.models import Announcement
from lostfound.models import Item
from marketplace.models import Product, ProductReport
from mentorship.models import MentorshipRequest
from roommates.models import RoommateProfile

User = get_user_model()


def apply_range(qs, start, end, field="created_at"):
    if start:
        qs = qs.filter(**{f"{field}__date__gte": start})
    if end:
        qs = qs.filter(**{f"{field}__date__lte": end})
    return qs


def summary(start=None, end=None):
    students = apply_range(User.objects.filter(is_staff=False), start, end, "date_joined")
    products = apply_range(Product.objects.all(), start, end)
    items = apply_range(Item.objects.all(), start, end)
    mentorship = apply_range(MentorshipRequest.objects.all(), start, end)
    return OrderedDict([
        ("total_students", students.count()),
        ("verified_students", students.filter(is_email_verified=True).count()),
        ("total_products", products.count()),
        ("sold_products", products.filter(status=Product.Status.SOLD).count()),
        ("lost_items", items.filter(item_type=Item.ItemType.LOST).count()),
        ("found_items", items.filter(item_type=Item.ItemType.FOUND).count()),
        ("recovered_items", items.filter(status=Item.Status.RECOVERED).count()),
        ("active_roommates", apply_range(RoommateProfile.objects.filter(is_active=True), start, end).count()),
        ("mentorship_requests", mentorship.count()),
        ("pending_requests", mentorship.filter(status=MentorshipRequest.Status.PENDING).count()),
        ("total_announcements", apply_range(Announcement.objects.all(), start, end).count()),
        ("reported_listings", apply_range(ProductReport.objects.filter(status=ProductReport.Status.OPEN),
                                          start, end).count()),
    ])


def _choice_counts(qs, field, choices):
    counts = {row[field]: row["n"] for row in qs.values(field).annotate(n=Count("id"))}
    return {"labels": [label for _, label in choices], "data": [counts.get(value, 0) for value, _ in choices]}


def charts(start=None, end=None):
    items = apply_range(Item.objects.all(), start, end)
    products = apply_range(Product.objects.all(), start, end)
    users = apply_range(User.objects.filter(is_staff=False), start, end, "date_joined")
    regs = users.annotate(day=TruncDate("date_joined")).values("day").annotate(n=Count("id")).order_by("day")
    return {
        "lostfound": {
            "labels": ["Lost", "Found", "Recovered"],
            "data": [items.filter(item_type="lost").count(), items.filter(item_type="found").count(),
                     items.filter(status="recovered").count()],
        },
        "products_by_category": _choice_counts(products, "category", Product.Category.choices),
        "available_vs_sold": _choice_counts(products, "status", Product.Status.choices),
        "registrations": {"labels": [r["day"].strftime("%d %b") for r in regs if r["day"]],
                          "data": [r["n"] for r in regs if r["day"]]},
        "mentorship_status": _choice_counts(apply_range(MentorshipRequest.objects.all(), start, end), "status",
                                            MentorshipRequest.Status.choices),
        "accommodation": _choice_counts(apply_range(RoommateProfile.objects.all(), start, end), "accommodation_type",
                                        RoommateProfile.Accommodation.choices),
    }
