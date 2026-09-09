from rest_framework import serializers

from apps.athletes.models import AthleteProfile
from apps.athletes.services import completed_sections
from apps.careers.serializers import AchievementSerializer, AthleticResultSerializer
from apps.education.models import Education
from apps.media_library.serializers import HighlightVideoSerializer
from apps.sports.models import AthleteSportProfile
from apps.sports.serializers import PositionSerializer, SportSerializer

from .models import Portfolio, SocialLink


class PublicEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ("school", "graduation_year", "intended_major")


class PublicSportSerializer(serializers.ModelSerializer):
    primary_sport = SportSerializer(read_only=True)
    positions = PositionSerializer(many=True, read_only=True)

    class Meta:
        model = AthleteSportProfile
        fields = (
            "primary_sport",
            "positions",
            "jersey_number",
            "height_cm",
            "weight_kg",
            "years_played",
        )


class PublicAthleteSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    sport = PublicSportSerializer(source="sport_profile", read_only=True)
    education = PublicEducationSerializer(read_only=True)
    achievements = AchievementSerializer(many=True, read_only=True)
    results = AthleticResultSerializer(many=True, read_only=True)
    highlights = HighlightVideoSerializer(many=True, read_only=True)

    class Meta:
        model = AthleteProfile
        fields = (
            "full_name",
            "city",
            "state",
            "current_team",
            "biography",
            "profile_photo_url",
            "sport",
            "education",
            "achievements",
            "results",
            "highlights",
        )


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ("id", "platform", "url")
        read_only_fields = ("id",)
        validators = []

    def validate_platform(self, value):
        value = value.strip().lower()
        queryset = SocialLink.objects.filter(
            portfolio__athlete__user=self.context["request"].user, platform=value
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A link for this platform already exists.")
        return value


class PortfolioSerializer(serializers.ModelSerializer):
    athlete = PublicAthleteSerializer(read_only=True)
    social_links = SocialLinkSerializer(many=True, read_only=True)
    completion_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "slug",
            "is_published",
            "completion_percentage",
            "story",
            "recruiting_status",
            "goals",
            "athlete",
            "social_links",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs.get("is_published", self.instance.is_published):
            missing = [
                name for name, done in completed_sections(self.instance.athlete).items() if not done
            ]
            if missing:
                raise serializers.ValidationError(
                    {"is_published": f"Complete onboarding: {', '.join(missing)}."}
                )
            if not attrs.get("story", self.instance.story).strip():
                raise serializers.ValidationError({"story": "Add your story before publishing."})
        return attrs
