from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from lostfound.models import Item
from marketplace.models import Product

from .emails import send_verification_otp
from .forms import LoginForm, OTPForm, ProfileForm, RegistrationForm, UserUpdateForm
from .models import EmailOTP

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        send_verification_otp(user)
        login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
        messages.success(request, f"Welcome aboard! We sent a verification code to {user.email}.")
        return redirect("accounts:verify_otp")
    return render(request, "registration/register.html", {"form": form})


class CampusLoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@login_required
def verify_otp(request):
    if request.user.is_email_verified:
        return redirect("dashboard:home")
    form = OTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        otp = EmailOTP.objects.filter(user=request.user, is_used=False).first()
        if otp and otp.verify(form.cleaned_data["code"]):
            request.user.is_email_verified = True
            request.user.save(update_fields=["is_email_verified"])
            messages.success(request, "Email verified. Your campus is now unlocked!")
            return redirect("dashboard:home")
        if otp is None or otp.is_expired or otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            form.add_error("code", "This code has expired or is locked. Request a new one.")
        else:
            form.add_error("code", "Incorrect code. Please try again.")
    return render(request, "registration/verify_otp.html", {"form": form})


@login_required
@require_POST
def resend_otp(request):
    if not request.user.is_email_verified:
        send_verification_otp(request.user)
        messages.info(request, "A new code has been sent to your email.")
    return redirect("accounts:verify_otp")


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {
        "profile_user": request.user,
        "products": Product.objects.filter(seller=request.user)[:6],
        "items": Item.objects.filter(owner=request.user)[:6],
        "is_own": True,
    })


@login_required
def edit_profile(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/edit_profile.html", {"user_form": user_form, "profile_form": profile_form})


@login_required
def public_profile(request, username):
    profile_user = get_object_or_404(User.objects.select_related("profile"), username=username, is_active=True)
    return render(request, "accounts/profile.html", {
        "profile_user": profile_user,
        "products": Product.objects.filter(seller=profile_user, is_hidden=False)[:6],
        "items": Item.objects.filter(owner=profile_user)[:6],
        "is_own": profile_user == request.user,
    })
