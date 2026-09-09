from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class AthleteProfile(TimeStampedModel):
    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        NON_BINARY = "non_binary", "Non-binary"
        UNDISCLOSED = "undisclosed", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="athlete_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    current_team = models.CharField(max_length=150, blank=True)
    biography = models.TextField(blank=True, max_length=5000)
    profile_photo_url = models.URLField(blank=True, max_length=500)
    phone_number = models.CharField(max_length=30, blank=True)
    onboarding_status = models.CharField(
        max_length=20,
        default="not_started",
        choices=[
            ("not_started", "Not started"),
            ("in_progress", "In progress"),
            ("completed", "Completed"),
        ],
    )
    onboarding_step = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(3)])

    def __str__(self):
        return self.user.full_name
