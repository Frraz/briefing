"""Ferzion Discovery — URL configuration."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("api/v1/briefing/", include("apps.briefing.api.urls")),
    # path("painel/", include("apps.client_panel.urls")),
    # path("console/", include("apps.ferzion_console.urls")),
]

if settings.DEBUG:
    try:
        import debug_toolbar  # noqa: F401

        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    except ImportError:
        pass
