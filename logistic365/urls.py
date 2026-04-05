"""logistic365 URL Configuration"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("users/", include("users.urls", namespace="users")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("transport/", include("transport.urls", namespace="transport")),
    path("routes/", include("routes.urls", namespace="routes")),
    path("tracking/", include("tracking.urls", namespace="tracking")),
    path("reports/", include("reports.urls", namespace="reports")),
    path("references/", include("references.urls", namespace="references")),
    # API v1
    path("api/v1/orders/", include(("orders.api_urls", "orders-api"), namespace="orders-api")),
    path("api/v1/transport/", include(("transport.api_urls", "transport-api"), namespace="transport-api")),
    path("api/v1/routes/", include(("routes.api_urls", "routes-api"), namespace="routes-api")),
    path("api/v1/tracking/", include(("tracking.api_urls", "tracking-api"), namespace="tracking-api")),
    path("api/v1/references/", include(("references.api_urls", "references-api"), namespace="references-api")),
    path("api/v1/users/", include(("users.api_urls", "users-api"), namespace="users-api")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
