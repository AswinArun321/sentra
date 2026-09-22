from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect, render
from django.conf import settings
from rest_framework.permissions import BasePermission


class IsSENTRAAdminUser(BasePermission):
    """
    Allows access only to authenticated staff or superuser administrators.
    Never relies on email hardcoding or insecure flags.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


def admin_required(view_func):
    """
    Decorator for template views that ensures the user is logged in
    and possesses staff/admin status.
    Unauthenticated users are redirected to login.
    Authenticated non-staff users receive a 403 Forbidden page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            path = request.get_full_path()
            login_url = getattr(settings, 'LOGIN_URL', '/auth/login/')
            return redirect(f"{login_url}?{REDIRECT_FIELD_NAME}={path}")

        if not (request.user.is_staff or request.user.is_superuser):
            return render(
                request,
                'admin_panel/403.html',
                {
                    'error_title': 'Access Denied',
                    'error_message': 'Administrative privileges (staff or superuser) are required to access the SENTRA Admin Console.',
                },
                status=403
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view
