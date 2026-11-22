from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from notifications.models import Notification
from notifications.utils import notify

from .compatibility import compatibility
from .forms import RoommateFilterForm, RoommateProfileForm, RoommateRequestForm
from .models import RoommateProfile, RoommateRequest


def _my_profile(user):
    return RoommateProfile.objects.filter(user=user).first()


def browse_profiles(user, params):
    qs = RoommateProfile.objects.filter(is_active=True).exclude(user=user).select_related("user", "user__profile")
    form = RoommateFilterForm(params)
    sort = "match"
    if form.is_valid():
        d = form.cleaned_data
        if d["q"]:
            qs = qs.filter(Q(headline__icontains=d["q"]) | Q(about__icontains=d["q"]) |
                           Q(user__first_name__icontains=d["q"]) | Q(user__last_name__icontains=d["q"]))
        if d["location"]:
            qs = qs.filter(preferred_location=d["location"])
        if d["accommodation"]:
            qs = qs.filter(accommodation_type=d["accommodation"])
        if d["food"]:
            qs = qs.filter(food_preference=d["food"])
        if d["sleep"]:
            qs = qs.filter(sleep_schedule=d["sleep"])
        if d["max_budget"] is not None:
            qs = qs.filter(budget_min__lte=d["max_budget"])
        sort = d["sort"] or "match"
    mine = _my_profile(user)
    results = []
    for p in qs:
        p.compat = compatibility(mine, p) if mine else None
        results.append(p)
    if sort == "match" and mine:
        results.sort(key=lambda p: p.compat["score"], reverse=True)
    elif sort == "budget":
        results.sort(key=lambda p: p.budget_min)
    return results, form, mine


@login_required
def profile_list(request):
    results, form, mine = browse_profiles(request.user, request.GET)
    saved_ids = set(request.user.saved_roommates.values_list("id", flat=True))
    return render(request, "roommates/list.html", {"profiles": results, "filter_form": form, "my_profile": mine,
                                                   "saved_ids": saved_ids})


@login_required
@require_GET
def api_filter(request):
    results, _, mine = browse_profiles(request.user, request.GET)
    saved_ids = set(request.user.saved_roommates.values_list("id", flat=True))
    html = render_to_string("roommates/_cards.html", {"profiles": results, "my_profile": mine,
                                                      "saved_ids": saved_ids}, request=request)
    data = [{"id": p.id, "name": p.user.display_name, "headline": p.headline,
             "compatibility": p.compat["score"] if p.compat else None,
             "matching": p.compat["matching"] if p.compat else []} for p in results]
    return JsonResponse({"count": len(data), "results": data, "html": html})


@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(RoommateProfile.objects.select_related("user", "user__profile"), pk=pk)
    if not profile.is_active and profile.user != request.user:
        raise PermissionDenied("This profile is not active.")
    mine = _my_profile(request.user)
    compat = compatibility(mine, profile) if mine and mine != profile else None
    pending = RoommateRequest.objects.filter(sender=request.user, receiver=profile.user,
                                             status=RoommateRequest.Status.PENDING).exists()
    return render(request, "roommates/detail.html", {
        "profile": profile, "compat": compat, "my_profile": mine, "request_form": RoommateRequestForm(),
        "already_requested": pending, "is_saved": profile.saved_by.filter(pk=request.user.pk).exists()})


@login_required
def my_profile_edit(request):
    instance = _my_profile(request.user)
    form = RoommateProfileForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        messages.success(request, "Roommate profile saved.")
        return redirect("roommates:list")
    return render(request, "roommates/form.html", {"form": form, "is_new": instance is None})


@login_required
@require_POST
def send_request(request, pk):
    profile = get_object_or_404(RoommateProfile, pk=pk, is_active=True)
    if profile.user == request.user:
        messages.error(request, "You can't send a request to yourself.")
        return redirect(profile)
    if RoommateRequest.objects.filter(sender=request.user, receiver=profile.user,
                                      status=RoommateRequest.Status.PENDING).exists():
        messages.info(request, "You already have a pending request with this student.")
        return redirect(profile)
    form = RoommateRequestForm(request.POST)
    if form.is_valid():
        req = form.save(commit=False)
        req.sender, req.receiver = request.user, profile.user
        req.save()
        notify(profile.user, Notification.Type.ROOMMATE_REQUEST, "New roommate request",
               f"{request.user.display_name} wants to be your roommate.", reverse("roommates:requests"), request.user)
        messages.success(request, "Roommate request sent!")
    return redirect(profile)


@login_required
@require_POST
def respond_request(request, pk, action):
    req = get_object_or_404(RoommateRequest, pk=pk)
    if req.receiver != request.user:
        raise PermissionDenied("Only the receiver can respond to this request.")
    if req.status != RoommateRequest.Status.PENDING or action not in ("accept", "reject"):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "Request already handled"}, status=400)
        return redirect("roommates:requests")
    req.status = RoommateRequest.Status.ACCEPTED if action == "accept" else RoommateRequest.Status.REJECTED
    req.save(update_fields=["status", "updated_at"])
    ntype = Notification.Type.REQUEST_ACCEPTED if action == "accept" else Notification.Type.REQUEST_REJECTED
    notify(req.sender, ntype, f"Roommate request {req.get_status_display().lower()}",
           f"{request.user.display_name} {req.get_status_display().lower()} your roommate request.",
           reverse("roommates:requests"), request.user)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "status": req.status, "label": req.get_status_display()})
    messages.success(request, f"Request {req.get_status_display().lower()}.")
    return redirect("roommates:requests")


@login_required
def requests_view(request):
    return render(request, "roommates/requests.html", {
        "received": request.user.roommate_requests_received.select_related("sender", "sender__roommate_profile"),
        "sent": request.user.roommate_requests_sent.select_related("receiver", "receiver__roommate_profile"),
    })


@login_required
@require_POST
def api_toggle_save(request, pk):
    profile = get_object_or_404(RoommateProfile, pk=pk)
    if profile.saved_by.filter(pk=request.user.pk).exists():
        profile.saved_by.remove(request.user)
        saved = False
    else:
        profile.saved_by.add(request.user)
        saved = True
    return JsonResponse({"ok": True, "saved": saved})


@login_required
def saved_profiles(request):
    mine = _my_profile(request.user)
    profiles = list(request.user.saved_roommates.select_related("user"))
    for p in profiles:
        p.compat = compatibility(mine, p) if mine else None
    return render(request, "roommates/saved.html", {"profiles": profiles, "my_profile": mine,
                                                    "saved_ids": {p.id for p in profiles}})
