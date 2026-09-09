from rest_framework import serializers

from .models import AthleteSportProfile, Position, Sport


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "sport", "name")


class SportSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)

    class Meta:
        model = Sport
        fields = ("id", "name", "slug", "positions")


class AthleteSportProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteSportProfile
        fields = (
            "id",
            "primary_sport",
            "positions",
            "jersey_number",
            "height_cm",
            "weight_kg",
            "years_played",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        sport = attrs.get("primary_sport", self.instance.primary_sport if self.instance else None)
        positions = attrs.get("positions", self.instance.positions.all() if self.instance else [])
        if any(position.sport_id != getattr(sport, "pk", None) for position in positions):
            raise serializers.ValidationError(
                {
                    "positions": "Positions must belong to the primary sport. "
                    "Send new positions when changing sports."
                }
            )
        return attrs
