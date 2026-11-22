from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import ItemFilterForm, ItemForm
from .matching import find_matches, record_matches
from .models import Item


def filter_items(params):
    qs = Item.objects.select_related("owner")
    form = ItemFilterForm(params)
    if form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            qs = qs.filter(Q(title__icontains=data["q"]) | Q(description__icontains=data["q"]) |
                           Q(location__icontains=data["q"]))
        if data["item_type"]:
            qs = qs.filter(item_type=data["item_type"])
        if data["category"]:
            qs = qs.filter(category=data["category"])
        if data["status"]:
            qs = qs.filter(status=data["status"])
    return qs, form


def _get_own_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user and not request.user.is_site_admin:
        raise PermissionDenied("You can only manage your own listings.")
    return item


@login_required
def item_list(request):
    qs, form = filter_items(request.GET)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "lostfound/list.html", {"page_obj": page, "filter_form": form})


@login_required
@require_GET
def api_search(request):
    qs, _ = filter_items(request.GET)
    qs = qs[:30]
    html = render_to_string("lostfound/_cards.html", {"items": qs}, request=request)
    data = [{"id": i.id, "title": i.title, "type": i.item_type, "category": i.get_category_display(),
             "location": i.location, "date": i.date.isoformat(), "status": i.status} for i in qs]
    return JsonResponse({"count": len(data), "results": data, "html": html})


@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item.objects.select_related("owner"), pk=pk)
    matches = find_matches(item) if item.status == Item.Status.OPEN and item.owner == request.user else []
    return render(request, "lostfound/detail.html", {"item": item, "matches": matches})


@login_required
def item_create(request):
    initial = {"item_type": request.GET.get("type", "lost"), "date": timezone.localdate()}
    form = ItemForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.owner = request.user
        item.save()
        matches = record_matches(item)
        msg = "Listing published."
        if matches:
            msg += f" We found {len(matches)} potential match(es) — check below!"
        messages.success(request, msg)
        return redirect(item)
    return render(request, "lostfound/form.html", {"form": form, "title": "Report an item"})


@login_required
def item_edit(request, pk):
    item = _get_own_item(request, pk)
    form = ItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        record_matches(item)
        messages.success(request, "Listing updated.")
        return redirect(item)
    return render(request, "lostfound/form.html", {"form": form, "title": "Edit listing", "item": item})


@login_required
def item_delete(request, pk):
    item = _get_own_item(request, pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Listing deleted.")
        return redirect("lostfound:my_items")
    return render(request, "confirm_delete.html", {"object": item, "cancel_url": item.get_absolute_url()})


@login_required
@require_POST
def api_update_status(request, pk):
    item = _get_own_item(request, pk)
    status = request.POST.get("status", Item.Status.RECOVERED)
    if status not in Item.Status.values:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)
    item.status = status
    item.recovered_at = timezone.now() if status == Item.Status.RECOVERED else None
    item.save(update_fields=["status", "recovered_at", "updated_at"])
    return JsonResponse({"ok": True, "status": item.status, "label": item.get_status_display()})


@login_required
def my_items(request):
    items = Item.objects.filter(owner=request.user)
    return render(request, "lostfound/my_items.html", {"items": items})
