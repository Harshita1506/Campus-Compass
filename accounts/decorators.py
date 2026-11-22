from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """Allow only staff / admin-role users. Others get HTTP 403."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_site_admin:
            raise PermissionDenied("Administrator access required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def senior_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_senior or request.user.is_site_admin):
            raise PermissionDenied("Only seniors / alumni can access this page.")
        return view_func(request, *args, **kwargs)

    return _wrapped
