from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class Education(TimeStampedModel):
    athlete = models.OneToOneField(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="education"
    )
    school = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)]
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
    )
    intended_major = models.CharField(max_length=150, blank=True)
    ncaa_id = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.athlete}: {self.school}"
