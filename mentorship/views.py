from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import senior_required
from notifications.models import Notification
from notifications.utils import notify

from .filters import SeniorFilter
from .forms import MentorshipRequestForm, ResponseForm, SeniorProfileForm
from .models import MentorshipRequest, SeniorProfile


@login_required
def senior_list(request):
    base = SeniorProfile.objects.select_related("user", "user__profile").prefetch_related("skills").distinct()
    flt = SeniorFilter(request.GET, queryset=base)
    for field in flt.form.fields.values():
        field.widget.attrs.setdefault("class", "form-select" if hasattr(field, "choices") else "form-control")
    years = SeniorProfile.objects.values_list("graduation_year", flat=True).distinct().order_by("-graduation_year")
    return render(request, "mentorship/list.html", {"filter": flt, "seniors": flt.qs, "years": years})


@login_required
def senior_detail(request, pk):
    senior = get_object_or_404(SeniorProfile.objects.select_related("user").prefetch_related("skills"), pk=pk)
    pending = MentorshipRequest.objects.filter(student=request.user, senior=senior,
                                               status=MentorshipRequest.Status.PENDING).exists()
    return render(request, "mentorship/detail.html", {
        "senior": senior, "form": MentorshipRequestForm(), "already_requested": pending,
        "is_self": senior.user == request.user})


@login_required
@require_POST
def send_request(request, pk):
    senior = get_object_or_404(SeniorProfile, pk=pk)
    if senior.user == request.user:
        messages.error(request, "You can't request mentorship from yourself.")
        return redirect(senior)
    if not senior.is_available:
        messages.error(request, "This senior is not accepting requests right now.")
        return redirect(senior)
    if MentorshipRequest.objects.filter(student=request.user, senior=senior,
                                        status=MentorshipRequest.Status.PENDING).exists():
        messages.info(request, "You already have a pending request with this senior.")
        return redirect(senior)
    form = MentorshipRequestForm(request.POST)
    if form.is_valid():
        req = form.save(commit=False)
        req.student, req.senior = request.user, senior
        req.save()
        notify(senior.user, Notification.Type.MENTORSHIP_REQUEST, "New mentorship request",
               f"{request.user.display_name} asked for guidance on '{req.topic}'.",
               reverse("mentorship:incoming"), request.user)
        messages.success(request, "Mentorship request sent!")
    else:
        messages.error(request, "Please fill in the topic and message.")
    return redirect(senior)


@login_required
def my_requests(request):
    reqs = request.user.mentorship_requests_sent.select_related("senior", "senior__user")
    return render(request, "mentorship/my_requests.html", {"requests": reqs})


@senior_required
def incoming_requests(request):
    profile = SeniorProfile.objects.filter(user=request.user).first()
    reqs = profile.requests.select_related("student", "student__profile") if profile else []
    return render(request, "mentorship/incoming.html", {"requests": reqs, "profile": profile,
                                                        "response_form": ResponseForm()})


@login_required
@require_POST
def respond_request(request, pk, action):
    req = get_object_or_404(MentorshipRequest.objects.select_related("senior__user"), pk=pk)
    if req.senior.user != request.user:
        raise PermissionDenied("Only the requested senior can respond.")
    if req.status != MentorshipRequest.Status.PENDING or action not in ("accept", "reject"):
        messages.info(request, "This request was already handled.")
        return redirect("mentorship:incoming")
    form = ResponseForm(request.POST)
    note = form.cleaned_data["response_note"] if form.is_valid() else ""
    req.status = MentorshipRequest.Status.ACCEPTED if action == "accept" else MentorshipRequest.Status.REJECTED
    req.response_note, req.responded_at = note, timezone.now()
    req.save()
    ntype = Notification.Type.REQUEST_ACCEPTED if action == "accept" else Notification.Type.REQUEST_REJECTED
    notify(req.student, ntype, f"Mentorship request {req.get_status_display().lower()}",
           f"{request.user.display_name} {req.get_status_display().lower()} your request on '{req.topic}'.",
           reverse("mentorship:my_requests"), request.user)
    messages.success(request, f"Request {req.get_status_display().lower()}.")
    return redirect("mentorship:incoming")


@senior_required
def edit_senior_profile(request):
    instance = SeniorProfile.objects.filter(user=request.user).first()
    form = SeniorProfileForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        form.save_skills(profile)
        messages.success(request, "Senior profile saved.")
        return redirect(profile)
    return render(request, "mentorship/form.html", {"form": form, "is_new": instance is None})
