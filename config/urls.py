from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.sports.views import PositionViewSet, SportViewSet

router = DefaultRouter()
router.register("sports", SportViewSet)
router.register("positions", PositionViewSet)

urlpatterns = [
    path("api/v1/athletes/", include("apps.athletes.urls")),
    path("api/v1/portfolios/", include("apps.portfolios.urls")),
    path("api/v1/", include(router.urls)),
    path("admin/", admin.site.urls),
    path("api/v1/health/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
]
