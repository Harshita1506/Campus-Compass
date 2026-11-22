"""Shared validators: secure image uploads and safe external URLs."""
import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def validate_image_file(file):
    """Limit size and extension. Content is additionally verified by Pillow via ImageField."""
    if not file:
        return
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"Image too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.")
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Unsupported file type. Use JPG, PNG, WEBP or GIF.")


def _validate_domain(value, domains, label):
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ValidationError(f"{label} URL must start with https://")
    host = (parsed.hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in domains):
        raise ValidationError(f"Enter a valid {label} URL ({', '.join(domains)}).")


def validate_linkedin_url(value):
    _validate_domain(value, ["linkedin.com"], "LinkedIn")


def validate_github_url(value):
    _validate_domain(value, ["github.com"], "GitHub")


def validate_safe_external_url(value):
    """Only allow http(s) links (blocks javascript:, data:, etc.)."""
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Only http:// or https:// links are allowed.")
