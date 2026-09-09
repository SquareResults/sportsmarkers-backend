from rest_framework import serializers

from .models import Achievement, AthleticResult


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ("id", "title", "organization", "date", "description")
        read_only_fields = ("id",)


class AthleticResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleticResult
        fields = ("id", "sport", "event", "metric", "value", "unit", "date")
        read_only_fields = ("id",)
