from datetime import date

from rest_framework import serializers

from .models import AthleteProfile


class AthleteProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteProfile
        fields = (
            "id",
            "date_of_birth",
            "city",
            "state",
            "gender",
            "current_team",
            "biography",
            "profile_photo_url",
            "phone_number",
            "onboarding_status",
            "onboarding_step",
        )
        read_only_fields = ("id", "onboarding_status", "onboarding_step")

    def validate_date_of_birth(self, value):
        if value and value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value


class OnboardingSummarySerializer(serializers.Serializer):
    completed_sections = serializers.ListField(child=serializers.CharField())
    missing_sections = serializers.ListField(child=serializers.CharField())
    onboarding_status = serializers.CharField()
    onboarding_step = serializers.IntegerField()
    completion_percentage = serializers.IntegerField()
