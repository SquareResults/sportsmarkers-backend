from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from apps.common.models import TimeStampedModel

from .managers import UserManager


class User(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ATHLETE = "athlete", "Athlete"
        RECRUITER = "recruiter", "Recruiter"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATHLETE)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_user_email_ci")]

    def __str__(self) -> str:
        return self.email
