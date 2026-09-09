import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.mark.django_db
def test_registers_an_athlete():
    response = APIClient().post(
        reverse("register"),
        {
            "email": "athlete@example.com",
            "full_name": "Jordan Athlete",
            "password": "A-secure-password-2026!",
            "confirm_password": "A-secure-password-2026!",
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(email="athlete@example.com")
    assert user.role == User.Role.ATHLETE
    assert user.check_password("A-secure-password-2026!")


@pytest.mark.django_db
def test_rejects_mismatched_passwords():
    response = APIClient().post(
        reverse("register"),
        {
            "email": "athlete@example.com",
            "full_name": "Jordan Athlete",
            "password": "A-secure-password-2026!",
            "confirm_password": "Different-password-2026!",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not User.objects.exists()


@pytest.mark.django_db
def test_returns_authenticated_user():
    user = User.objects.create_user(
        email="athlete@example.com",
        full_name="Jordan Athlete",
        password="A-secure-password-2026!",
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get(reverse("me"))

    assert response.status_code == 200
    assert response.data["email"] == user.email
