import os
import uuid

from django.utils.deconstruct import deconstructible


@deconstructible
class UploadTo:
    """Store uploads under a folder with a random UUID filename (no user-controlled names)."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        return f"{self.folder}/{uuid.uuid4().hex}{ext}"


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get(
        "accept", ""
    )
