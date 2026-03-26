from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def root_redirect(request):
    if request.user.is_authenticated:
        if request.user.login_role == "admin":
            return redirect("admin_app:main-dashboard")
        return redirect("user_app:main-dashboard")
    return redirect("login")


urlpatterns = [
    # ROOT
    path("", root_redirect, name="root"),

    # DJANGO ADMIN (TEST / STAFF ONLY)
    path("penro/django/admin/", admin.site.urls),

    # AUTH
    path("auth/", include("accounts.urls")),

    # ROLE DASHBOARDS
    path("admin/", include("admin_app.urls")),
    path("user/", include("user_app.urls")),

    # NOTIFICATIONS API
    path("", include("notifications.urls")),
    
    # DOCUMENT TRACKING
    path("documents/", include("document_tracking.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    # Serve media files in development mode (only when using local storage)
    if not getattr(settings, 'CLOUDINARY_ENABLED', False):
        urlpatterns += static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT
        )
