from django.conf import settings
from django.core.mail import send_mail

from .models import EmailOTP


def send_verification_otp(user):
    _, code = EmailOTP.generate_for(user)
    send_mail(
        subject="Your Campus Compass verification code",
        message=(
            f"Hi {user.display_name},\n\n"
            f"Your Campus Compass verification code is: {code}\n"
            f"It expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n"
            "If you did not create an account, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return code
