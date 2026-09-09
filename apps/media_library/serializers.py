from rest_framework import serializers

from .models import HighlightVideo


class HighlightVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighlightVideo
        fields = ("id", "title", "url", "description")
        read_only_fields = ("id",)
