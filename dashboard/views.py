from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from announcements.models import Announcement
from locator.forms import BuildingForm, DepartmentForm, RoomForm
from locator.models import Building, Department, Room
from lostfound.models import Item, ItemMatch
from marketplace.models import Enquiry, Product, ProductReport, SavedProduct
from mentorship.models import MentorshipRequest, SeniorProfile
from notifications.models import Notification
from notifications.utils import notify
from roommates.models import RoommateProfile, RoommateRequest

from .forms import DateRangeForm
from .reports import REPORTS, csv_response
from .stats import charts, summary

User = get_user_model()


# ---------------------------------------------------------------- student dashboard
@login_required
def home(request):
    user = request.user
    senior = SeniorProfile.objects.filter(user=user).first()
    context = {
        "stats": {
            "listings": Product.objects.filter(seller=user).exclude(status=Product.Status.SOLD).count(),
            "saved": SavedProduct.objects.filter(user=user).count(),
            "items": Item.objects.filter(owner=user, status=Item.Status.OPEN).count(),
            "unread": user.notifications.filter(is_read=False).count(),
            "roommate_pending": RoommateRequest.objects.filter(receiver=user, status="pending").count(),
            "mentorship_sent": MentorshipRequest.objects.filter(student=user).count(),
        },
        "announcements": Announcement.objects.filter(is_published=True)[:4],
        "recent_products": Product.objects.filter(is_hidden=False, status="available").exclude(seller=user)[:4],
        "matches": ItemMatch.objects.filter(Q(lost_item__owner=user) | Q(found_item__owner=user)).select_related(
            "lost_item", "found_item")[:4],
        "notifications": user.notifications.all()[:5],
        "has_roommate_profile": RoommateProfile.objects.filter(user=user).exists(),
        "senior_profile": senior,
        "senior_pending": senior.requests.filter(status="pending").count() if senior else 0,
    }
    return render(request, "dashboard.html", context)


# ---------------------------------------------------------------- admin dashboard
META = {
    "total_students": ("Total students", "bi-people", "bg-indigo-soft"),
    "verified_students": ("Verified students", "bi-patch-check", "bg-green-soft"),
    "total_products": ("Marketplace products", "bi-bag", "bg-lavender"),
    "sold_products": ("Sold products", "bi-bag-check", "bg-blue-soft"),
    "lost_items": ("Lost items", "bi-exclamation-circle", "bg-rose-soft"),
    "found_items": ("Found items", "bi-hand-thumbs-up", "bg-green-soft"),
    "recovered_items": ("Recovered items", "bi-arrow-repeat", "bg-indigo-soft"),
    "active_roommates": ("Active roommate profiles", "bi-house-heart", "bg-lavender"),
    "mentorship_requests": ("Mentorship requests", "bi-mortarboard", "bg-blue-soft"),
    "pending_requests": ("Pending requests", "bi-hourglass-split", "bg-amber-soft"),
    "total_announcements": ("Announcements", "bi-megaphone", "bg-indigo-soft"),
    "reported_listings": ("Open reported listings", "bi-flag", "bg-rose-soft"),
}

def _range(request):
    form = DateRangeForm(request.GET or None)
    if form.is_valid():
        return form, form.cleaned_data.get("start"), form.cleaned_data.get("end")
    return form, None, None


@admin_required
def admin_index(request):
    form, start, end = _range(request)
    data = summary(start, end)
    cards = [(META[key][0], value, META[key][1], META[key][2]) for key, value in data.items()]
    return render(request, "dashboard/admin_index.html", {
        "form": form, "summary_cards": cards, "reports": REPORTS,
        "query": request.GET.urlencode(),
        "recent_reports": ProductReport.objects.filter(status="open").select_related("product", "reporter")[:5],
        "recent_users": User.objects.filter(is_staff=False).order_by("-date_joined")[:5],
    })


@admin_required
def admin_stats_api(request):
    _, start, end = _range(request)
    return JsonResponse({"summary": summary(start, end), "charts": charts(start, end)})


@admin_required
def export_csv(request, report):
    if report not in REPORTS:
        raise Http404("Unknown report")
    _, start, end = _range(request)
    return csv_response(report, start, end)


# ---------------------------------------------------------------- moderation
@admin_required
def moderation(request):
    status = request.GET.get("status", "open")
    reports = ProductReport.objects.select_related("product", "product__seller", "reporter")
    if status in ProductReport.Status.values:
        reports = reports.filter(status=status)
    hidden = Product.objects.filter(is_hidden=True).select_related("seller")
    return render(request, "dashboard/moderation.html", {
        "reports": reports, "status": status, "hidden_products": hidden,
        "recent_items": Item.objects.select_related("owner")[:15]})


@admin_required
@require_POST
def moderate_report(request, pk, action):
    rep = get_object_or_404(ProductReport.objects.select_related("product"), pk=pk)
    product = rep.product
    if action == "hide":
        product.is_hidden = True
        product.save(update_fields=["is_hidden"])
        product.reports.filter(status="open").update(status=ProductReport.Status.ACTION_TAKEN)
        notify(product.seller, Notification.Type.MODERATION, "Your listing was hidden",
               f"'{product.title}' was hidden after a report review.", "", request.user)
        messages.success(request, f"'{product.title}' hidden.")
    elif action == "dismiss":
        rep.status = ProductReport.Status.DISMISSED
        rep.save(update_fields=["status"])
        messages.info(request, "Report dismissed.")
    elif action == "delete":
        title = product.title
        notify(product.seller, Notification.Type.MODERATION, "Your listing was removed",
               f"'{title}' was removed by moderators.", "", request.user)
        product.delete()
        messages.success(request, f"'{title}' deleted.")
    else:
        raise Http404
    return redirect("dashboard:moderation")


@admin_required
@require_POST
def toggle_product_visibility(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_hidden = not product.is_hidden
    product.save(update_fields=["is_hidden"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "hidden": product.is_hidden})
    messages.success(request, f"'{product.title}' is now {'hidden' if product.is_hidden else 'visible'}.")
    return redirect("dashboard:moderation")


@admin_required
@require_POST
def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    messages.success(request, "Lost & found listing removed.")
    return redirect("dashboard:moderation")


# ---------------------------------------------------------------- students
@admin_required
def students(request):
    qs = User.objects.select_related("profile").annotate(n_products=Count("products", distinct=True))
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) |
                       Q(last_name__icontains=q))
    role = request.GET.get("role", "")
    if role in User.Role.values:
        qs = qs.filter(role=role)
    page = Paginator(qs.order_by("-date_joined"), 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/students.html", {"page_obj": page, "q": q, "role": role,
                                                       "roles": User.Role.choices})


@admin_required
@require_POST
def student_action(request, pk, action):
    target = get_object_or_404(User, pk=pk)
    if target == request.user or target.is_superuser:
        messages.error(request, "You cannot modify this account here.")
        return redirect("dashboard:students")
    if action == "toggle_active":
        target.is_active = not target.is_active
        target.save(update_fields=["is_active"])
    elif action == "verify":
        target.is_email_verified = True
        target.save(update_fields=["is_email_verified"])
    elif action == "set_role":
        role = request.POST.get("role")
        if role not in User.Role.values:
            raise Http404
        target.role = role
        target.is_staff = role == User.Role.ADMIN
        target.save(update_fields=["role", "is_staff"])
    else:
        raise Http404
    messages.success(request, f"Updated {target.username}.")
    return redirect(request.POST.get("next") or reverse("dashboard:students"))


# ---------------------------------------------------------------- buildings & rooms
@admin_required
def buildings(request):
    return render(request, "dashboard/buildings.html", {
        "buildings": Building.objects.annotate(n_rooms=Count("rooms")),
        "rooms": Room.objects.select_related("building", "department")[:200],
        "departments": Department.objects.select_related("building")})


def _model_form_view(request, form_class, instance, title):
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{title} saved.")
        return redirect("dashboard:buildings")
    return render(request, "generic_form.html", {"form": form, "title": title, "cancel_url": reverse("dashboard:buildings")})


@admin_required
def building_form(request, pk=None):
    instance = get_object_or_404(Building, pk=pk) if pk else None
    return _model_form_view(request, BuildingForm, instance, "Building")


@admin_required
def room_form(request, pk=None):
    instance = get_object_or_404(Room, pk=pk) if pk else None
    return _model_form_view(request, RoomForm, instance, "Room")


@admin_required
def department_form(request, pk=None):
    instance = get_object_or_404(Department, pk=pk) if pk else None
    return _model_form_view(request, DepartmentForm, instance, "Department")


@admin_required
@require_POST
def delete_location(request, kind, pk):
    model = {"building": Building, "room": Room, "department": Department}.get(kind)
    if model is None:
        raise Http404
    get_object_or_404(model, pk=pk).delete()
    messages.success(request, f"{kind.title()} deleted.")
    return redirect("dashboard:buildings")


@admin_required
def enquiries(request):
    return render(request, "dashboard/enquiries.html",
                  {"enquiries": Enquiry.objects.select_related("product", "buyer")[:100]})
