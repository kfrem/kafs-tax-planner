from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.health import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="clients:client-list")),
    path("accounts/", include("firms.urls")),
    path("clients/", include("clients.urls")),
    path("advice/", include("advice.urls")),
    path("monitoring/", include("monitoring.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
