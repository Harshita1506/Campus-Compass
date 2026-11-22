from django.shortcuts import redirect
from django.urls import reverse


class EmailVerificationMiddleware:
    """Redirect logged-in users with an unverified email to the OTP page."""

    EXEMPT_PREFIXES = ("/accounts/verify", "/accounts/logout", "/accounts/resend-otp", "/static/", "/media/",
                       "/django-admin/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_email_verified
            and not user.is_superuser
            and request.path != "/"
            and not request.path.startswith(self.EXEMPT_PREFIXES)
        ):
            return redirect(reverse("accounts:verify_otp"))
        return self.get_response(request)
