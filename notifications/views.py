from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timesince import timesince
from django.views.decorators.http import require_GET, require_POST

from .models import Notification


@login_required
def notification_list(request):
    qs = request.user.notifications.select_related("actor")
    show = request.GET.get("show", "all")
    if show == "unread":
        qs = qs.filter(is_read=False)
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "notifications/list.html", {"page_obj": page, "show": show})


@login_required
def open_notification(request, pk):
    note = get_object_or_404(Notification, pk=pk, recipient=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    if note.url and url_has_allowed_host_and_scheme(note.url, allowed_hosts={request.get_host()}):
        return redirect(note.url)
    return redirect("notifications:list")


@login_required
@require_GET
def api_unread(request):
    qs = request.user.notifications.all()
    latest = [
        {"id": n.id, "title": n.title, "message": n.message, "icon": n.icon, "is_read": n.is_read,
         "time": timesince(n.created_at) + " ago", "url": f"/notifications/{n.id}/open/"}
        for n in qs[:6]
    ]
    return JsonResponse({"unread": qs.filter(is_read=False).count(), "latest": latest})


@login_required
@require_POST
def api_mark_read(request, pk):
    updated = Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    if not updated:
        return JsonResponse({"ok": False, "error": "Not found"}, status=404)
    return JsonResponse({"ok": True, "unread": request.user.notifications.filter(is_read=False).count()})


@login_required
@require_POST
def api_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"ok": True, "unread": 0})
