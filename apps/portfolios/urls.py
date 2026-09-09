from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AchievementViewSet,
    AthleticResultViewSet,
    HighlightVideoViewSet,
    MyPortfolioView,
    PublicPortfolioView,
    SocialLinkViewSet,
)

router = DefaultRouter()
router.register("achievements", AchievementViewSet)
router.register("results", AthleticResultViewSet)
router.register("highlights", HighlightVideoViewSet)
router.register("social-links", SocialLinkViewSet)
urlpatterns = [
    path("me/", MyPortfolioView.as_view(), name="portfolio-me"),
    path("public/<slug:slug>/", PublicPortfolioView.as_view(), name="portfolio-public"),
    path("", include(router.urls)),
]
