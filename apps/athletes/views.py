from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response

from apps.common.permissions import IsAthlete
from apps.education.serializers import EducationSerializer
from apps.sports.serializers import AthleteSportProfileSerializer

from .serializers import AthleteProfileSerializer, OnboardingSummarySerializer
from .services import ensure_athlete, onboarding_summary


class OnboardingSectionView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAthlete,)
    section = None
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_object(self):
        athlete = ensure_athlete(self.request.user)
        onboarding_summary(athlete)
        return getattr(athlete, self.section) if self.section else athlete

    def perform_update(self, serializer):
        instance = serializer.save()
        onboarding_summary(instance.athlete if self.section else instance)


@extend_schema(tags=["Onboarding"])
class PersonalView(OnboardingSectionView):
    serializer_class = AthleteProfileSerializer


@extend_schema(tags=["Onboarding"])
class SportProfileView(OnboardingSectionView):
    serializer_class = AthleteSportProfileSerializer
    section = "sport_profile"


@extend_schema(tags=["Onboarding"])
class EducationView(OnboardingSectionView):
    serializer_class = EducationSerializer
    section = "education"


@extend_schema(tags=["Onboarding"])
class OnboardingSummaryView(generics.GenericAPIView):
    permission_classes = (IsAthlete,)
    serializer_class = OnboardingSummarySerializer

    def get(self, request):
        return Response(onboarding_summary(ensure_athlete(request.user)))
