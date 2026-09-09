from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, viewsets

from apps.athletes.services import ensure_athlete
from apps.careers.models import Achievement, AthleticResult
from apps.careers.serializers import AchievementSerializer, AthleticResultSerializer
from apps.common.permissions import IsAthlete
from apps.media_library.models import HighlightVideo
from apps.media_library.serializers import HighlightVideoSerializer

from .models import Portfolio, SocialLink
from .serializers import PortfolioSerializer, SocialLinkSerializer


def portfolio_queryset():
    return Portfolio.objects.select_related(
        "athlete__user", "athlete__education", "athlete__sport_profile__primary_sport"
    ).prefetch_related(
        "athlete__sport_profile__positions",
        "athlete__sport_profile__primary_sport__positions",
        "athlete__achievements",
        "athlete__results",
        "athlete__highlights",
        "social_links",
    )


@extend_schema(tags=["Portfolios"])
class MyPortfolioView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAthlete,)
    serializer_class = PortfolioSerializer

    def get_object(self):
        athlete = ensure_athlete(self.request.user)
        return portfolio_queryset().get(athlete=athlete)

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            raise serializers.ValidationError({"slug": "This slug is already in use."}) from exc


@extend_schema(tags=["Public portfolios"], auth=[])
class PublicPortfolioView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    serializer_class = PortfolioSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return portfolio_queryset().filter(is_published=True, athlete__user__is_active=True)


class OwnedRecordViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAthlete,)
    owner_lookup = "athlete__user"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return self.queryset.filter(**{self.owner_lookup: self.request.user})

    def perform_create(self, serializer):
        athlete = ensure_athlete(self.request.user)
        owner = (
            {"portfolio": athlete.portfolio}
            if self.owner_lookup.startswith("portfolio")
            else {"athlete": athlete}
        )
        try:
            with transaction.atomic():
                serializer.save(**owner)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "A record with these unique values already exists."
            ) from exc

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "A record with these unique values already exists."
            ) from exc


@extend_schema(tags=["Portfolio records"])
class AchievementViewSet(OwnedRecordViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer


@extend_schema(tags=["Portfolio records"])
class AthleticResultViewSet(OwnedRecordViewSet):
    queryset = AthleticResult.objects.all()
    serializer_class = AthleticResultSerializer
    filterset_fields = ["sport"]


@extend_schema(tags=["Portfolio records"])
class HighlightVideoViewSet(OwnedRecordViewSet):
    queryset = HighlightVideo.objects.all()
    serializer_class = HighlightVideoSerializer


@extend_schema(tags=["Portfolio records"])
class SocialLinkViewSet(OwnedRecordViewSet):
    queryset = SocialLink.objects.all()
    serializer_class = SocialLinkSerializer
    owner_lookup = "portfolio__athlete__user"
