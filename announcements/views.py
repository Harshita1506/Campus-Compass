from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.decorators import admin_required
from notifications.models import Notification

from .filters import AnnouncementFilter
from .forms import AnnouncementForm
from .models import Announcement

User = get_user_model()


@login_required
def announcement_list(request):
    flt = AnnouncementFilter(request.GET, queryset=Announcement.objects.filter(is_published=True))
    for field in flt.form.fields.values():
        field.widget.attrs.setdefault("class", "form-select" if hasattr(field, "choices") else "form-control")
    page = Paginator(flt.qs, 10).get_page(request.GET.get("page"))
    pinned = Announcement.objects.filter(is_published=True, is_pinned=True)[:3]
    return render(request, "announcements/list.html", {"filter": flt, "page_obj": page, "pinned": pinned})


@login_required
def announcement_detail(request, pk):
    qs = Announcement.objects.all() if request.user.is_site_admin else Announcement.objects.filter(is_published=True)
    return render(request, "announcements/detail.html", {"announcement": get_object_or_404(qs, pk=pk)})


def _broadcast(announcement, actor):
    recipients = User.objects.filter(is_active=True, is_email_verified=True).exclude(pk=actor.pk)
    Notification.objects.bulk_create([
        Notification(recipient=u, actor=actor, notification_type=Notification.Type.ANNOUNCEMENT,
                     title=f"📢 {announcement.title}"[:150], message=announcement.body[:300],
                     url=announcement.get_absolute_url()) for u in recipients
    ])


@admin_required
def manage(request):
    return render(request, "announcements/manage.html", {"announcements": Announcement.objects.all()})


@admin_required
def announcement_create(request):
    form = AnnouncementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ann = form.save(commit=False)
        ann.author = request.user
        ann.save()
        if form.cleaned_data["notify_students"] and ann.is_published:
            _broadcast(ann, request.user)
        messages.success(request, "Announcement published.")
        return redirect("announcements:manage")
    return render(request, "generic_form.html", {"form": form, "title": "New announcement",
                                                 "cancel_url": reverse("announcements:manage")})


@admin_required
def announcement_edit(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, instance=ann)
    if request.method == "POST" and form.is_valid():
        form.save()
        if form.cleaned_data["notify_students"] and ann.is_published:
            _broadcast(ann, request.user)
        messages.success(request, "Announcement updated.")
        return redirect("announcements:manage")
    return render(request, "generic_form.html", {"form": form, "title": "Edit announcement",
                                                 "cancel_url": reverse("announcements:manage")})


@admin_required
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
        return redirect("announcements:manage")
    return render(request, "confirm_delete.html", {"object": ann, "cancel_url": "/announcements/manage/"})


@admin_required
def toggle_pin(request, pk):
    if request.method == "POST":
        ann = get_object_or_404(Announcement, pk=pk)
        ann.is_pinned = not ann.is_pinned
        ann.save(update_fields=["is_pinned", "updated_at"])
    return redirect("announcements:manage")
