from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class Sport(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(TimeStampedModel):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="positions")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["sport", "name"], name="unique_sport_position")
        ]

    def __str__(self):
        return f"{self.sport}: {self.name}"


class AthleteSportProfile(TimeStampedModel):
    athlete = models.OneToOneField(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="sport_profile"
    )
    primary_sport = models.ForeignKey(Sport, on_delete=models.PROTECT, null=True, blank=True)
    positions = models.ManyToManyField(Position, blank=True)
    jersey_number = models.CharField(max_length=10, blank=True)
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )
    years_played = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)]
    )

    def __str__(self):
        return str(self.athlete)
