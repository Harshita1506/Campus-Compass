from django.shortcuts import redirect, render

from announcements.models import Announcement
from lostfound.models import Item
from marketplace.models import Product
from mentorship.models import SeniorProfile
from roommates.models import RoommateProfile


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    stats = {
        "products": Product.objects.filter(is_hidden=False).count(),
        "items": Item.objects.count(),
        "roommates": RoommateProfile.objects.filter(is_active=True).count(),
        "seniors": SeniorProfile.objects.count(),
    }
    announcements = Announcement.objects.filter(is_published=True)[:3]
    return render(request, "landing.html", {"stats": stats, "announcements": announcements})


def error_403(request, exception=None):
    return render(request, "403.html", status=403)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)
