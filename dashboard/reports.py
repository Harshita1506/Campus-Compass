"""CSV report builders."""
import csv

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone

from lostfound.models import Item
from marketplace.models import Product, ProductReport
from mentorship.models import MentorshipRequest
from roommates.models import RoommateProfile

from .stats import apply_range, summary

User = get_user_model()


def _safe(value):
    """Prevent CSV/formula injection when opened in Excel."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


REPORTS = {
    "summary": "Summary statistics",
    "students": "Students",
    "products": "Marketplace products",
    "lostfound": "Lost & found items",
    "roommates": "Roommate profiles",
    "mentorship": "Mentorship requests",
    "reports": "Reported listings",
}


def build_rows(report, start, end):
    if report == "summary":
        return ["metric", "value"], [[k.replace("_", " ").title(), v] for k, v in summary(start, end).items()]
    if report == "students":
        qs = apply_range(User.objects.filter(is_staff=False).select_related("profile"), start, end, "date_joined")
        return (["username", "name", "email", "role", "branch", "year", "verified", "joined"],
                [[u.username, u.display_name, u.email, u.get_role_display(), u.profile.branch,
                  u.profile.get_academic_year_display(), u.is_email_verified, u.date_joined.date()] for u in qs])
    if report == "products":
        qs = apply_range(Product.objects.select_related("seller"), start, end)
        return (["id", "title", "seller", "category", "condition", "price", "status", "hidden", "created"],
                [[p.id, p.title, p.seller.username, p.get_category_display(), p.get_condition_display(), p.price,
                  p.get_status_display(), p.is_hidden, p.created_at.date()] for p in qs])
    if report == "lostfound":
        qs = apply_range(Item.objects.select_related("owner"), start, end)
        return (["id", "type", "title", "category", "location", "date", "status", "owner", "created"],
                [[i.id, i.get_item_type_display(), i.title, i.get_category_display(), i.location, i.date,
                  i.get_status_display(), i.owner.username, i.created_at.date()] for i in qs])
    if report == "roommates":
        qs = apply_range(RoommateProfile.objects.select_related("user"), start, end)
        return (["user", "budget_min", "budget_max", "location", "accommodation", "food", "sleep", "cleanliness",
                 "active"],
                [[p.user.username, p.budget_min, p.budget_max, p.get_preferred_location_display(),
                  p.get_accommodation_type_display(), p.get_food_preference_display(),
                  p.get_sleep_schedule_display(), p.get_cleanliness_display(), p.is_active] for p in qs])
    if report == "mentorship":
        qs = apply_range(MentorshipRequest.objects.select_related("student", "senior__user"), start, end)
        return (["id", "student", "senior", "topic", "status", "created", "responded"],
                [[r.id, r.student.username, r.senior.user.username, r.topic, r.get_status_display(),
                  r.created_at.date(), r.responded_at.date() if r.responded_at else ""] for r in qs])
    if report == "reports":
        qs = apply_range(ProductReport.objects.select_related("product", "reporter"), start, end)
        return (["id", "product", "reporter", "reason", "details", "status", "created"],
                [[r.id, r.product.title, r.reporter.username, r.get_reason_display(), r.details,
                  r.get_status_display(), r.created_at.date()] for r in qs])
    raise KeyError(report)


def csv_response(report, start=None, end=None):
    header, rows = build_rows(report, start, end)
    stamp = timezone.localdate().isoformat()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="campus_compass_{report}_{stamp}.csv"'
    response.write("﻿")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe(v) for v in row])
    return response
