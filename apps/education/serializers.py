from rest_framework import serializers

from .models import Education


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ("id", "school", "graduation_year", "gpa", "intended_major", "ncaa_id")
        read_only_fields = ("id",)
