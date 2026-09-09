from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, IntegrityError, transaction
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.athletes.management.commands.seed_demo import DEMO_EMAIL, DEMO_PASSWORD
from apps.athletes.models import AthleteProfile
from apps.careers.models import Achievement, AthleticResult
from apps.education.models import Education
from apps.media_library.models import HighlightVideo
from apps.portfolios.models import Portfolio, SocialLink
from apps.sports.models import AthleteSportProfile, Position, Sport

pytestmark = pytest.mark.django_db
PASSWORD = "A-secure-password-2026!"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="owner@example.com", password=PASSWORD, full_name="Owner Athlete"
    )


@pytest.fixture
def owner(client, user):
    client.force_authenticate(user)
    return client


@pytest.fixture
def demo(settings):
    settings.DEBUG = True
    call_command("seed_demo", stdout=StringIO())
    return User.objects.get(email=DEMO_EMAIL)


def registration(**overrides):
    return {
        "email": "new@example.com",
        "full_name": "New Athlete",
        "password": PASSWORD,
        "confirm_password": PASSWORD,
        **overrides,
    }


def test_registration_creates_all_sections_and_ignores_privilege_escalation(client):
    response = client.post(
        reverse("register"), registration(role="admin", is_staff=True), format="json"
    )
    assert response.status_code == 201
    account = User.objects.get(email="new@example.com")
    assert account.role == "athlete" and not account.is_staff
    assert account.athlete_profile.sport_profile and account.athlete_profile.education
    assert not account.athlete_profile.portfolio.is_published
    assert "password" not in response.data


@pytest.mark.parametrize("password", ["12345678", "password", "short", "new@example.com"])
def test_password_strength(client, password):
    response = client.post(
        reverse("register"),
        registration(password=password, confirm_password=password),
        format="json",
    )
    assert response.status_code == 400
    assert "password" in response.data["error"]["details"]


def test_duplicate_email_case_insensitive(client, user):
    response = client.post(
        reverse("register"), registration(email="OWNER@example.com"), format="json"
    )
    assert response.status_code == 400
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="OWNER@EXAMPLE.COM", password=PASSWORD)


def test_jwt_login_refresh_rotation_logout(client, user):
    assert client.get(reverse("me")).status_code == 401
    tokens = client.post(
        reverse("token-obtain-pair"),
        {"email": "OWNER@example.com", "password": PASSWORD},
        format="json",
    )
    assert tokens.status_code == 200
    client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens.data["access"])
    assert client.get(reverse("me")).data["id"] == str(user.pk)
    refreshed = client.post(
        reverse("token-refresh"), {"refresh": tokens.data["refresh"]}, format="json"
    )
    assert refreshed.status_code == 200
    assert (
        client.post(reverse("token-refresh"), {"refresh": tokens.data["refresh"]}).status_code
        == 401
    )
    assert client.post(reverse("logout"), {"refresh": refreshed.data["refresh"]}).status_code == 204
    assert (
        client.post(reverse("token-refresh"), {"refresh": refreshed.data["refresh"]}).status_code
        == 401
    )


def test_logout_cannot_blacklist_another_users_token(owner):
    other = User.objects.create_user(email="other@example.com", password=PASSWORD)
    from rest_framework_simplejwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(other))
    assert owner.post(reverse("logout"), {"refresh": token}).status_code == 400
    assert APIClient().post(reverse("token-refresh"), {"refresh": token}).status_code == 200
    assert owner.post(reverse("logout"), {"refresh": "invalid"}).status_code == 400


def test_account_update_protects_identity_and_role(owner, user):
    response = owner.patch(
        reverse("me"),
        {"full_name": "Updated", "email": "stolen@example.com", "role": "admin", "is_staff": True},
        format="json",
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.full_name == "Updated" and user.email == "owner@example.com"
    assert user.role == "athlete" and not user.is_staff


def test_onboarding_flow_and_validation(owner):
    initial = owner.get(reverse("athlete-onboarding")).data
    assert initial["missing_sections"] == ["personal", "sport", "education"]
    assert initial["onboarding_step"] == 0
    assert (
        owner.patch(
            reverse("athlete-me"), {"date_of_birth": "2999-01-01"}, format="json"
        ).status_code
        == 400
    )
    personal = owner.patch(
        reverse("athlete-me"),
        {
            "date_of_birth": "2008-02-01",
            "city": "Phoenix",
            "state": "AZ",
            "gender": "undisclosed",
            "onboarding_step": 3,
        },
        format="json",
    )
    assert personal.status_code == 200 and personal.data["onboarding_step"] == 1
    sport = Sport.objects.create(name="Basketball", slug="basketball")
    position = Position.objects.create(sport=sport, name="Guard")
    other_sport = Sport.objects.create(name="Soccer", slug="soccer")
    wrong_position = Position.objects.create(sport=other_sport, name="Forward")
    endpoint = reverse("athlete-sport")
    assert (
        owner.patch(
            endpoint,
            {"primary_sport": str(sport.pk), "positions": [str(wrong_position.pk)]},
            format="json",
        ).status_code
        == 400
    )
    assert owner.patch(endpoint, {"height_cm": -1}, format="json").status_code == 400
    assert (
        owner.patch(
            endpoint,
            {
                "primary_sport": str(sport.pk),
                "positions": [str(position.pk)],
                "height_cm": 180,
                "weight_kg": 70,
                "years_played": 0,
            },
            format="json",
        ).status_code
        == 200
    )
    assert (
        owner.patch(endpoint, {"primary_sport": str(other_sport.pk)}, format="json").status_code
        == 400
    )
    assert (
        owner.patch(reverse("athlete-education"), {"gpa": "4.01"}, format="json").status_code == 400
    )
    assert (
        owner.patch(
            reverse("athlete-education"),
            {"school": "School", "graduation_year": 2027, "gpa": "3.90"},
            format="json",
        ).status_code
        == 200
    )
    summary = owner.get(reverse("athlete-onboarding")).data
    assert summary["missing_sections"] == [] and summary["completion_percentage"] == 100
    assert summary["onboarding_status"] == "completed" and summary["onboarding_step"] == 3
    owner.patch(reverse("athlete-education"), {"school": ""}, format="json")
    assert owner.get(reverse("athlete-onboarding")).data["missing_sections"] == ["education"]


@pytest.mark.parametrize(
    "name",
    [
        "athlete-me",
        "athlete-sport",
        "athlete-education",
        "athlete-onboarding",
        "portfolio-me",
        "achievement-list",
        "athleticresult-list",
        "highlightvideo-list",
        "sociallink-list",
    ],
)
def test_private_endpoints_require_authentication(client, name):
    assert client.get(reverse(name)).status_code == 401


def test_non_athlete_cannot_use_athlete_endpoints(client):
    account = User.objects.create_user(email="recruiter@example.com", role="recruiter")
    client.force_authenticate(account)
    assert client.get(reverse("athlete-me")).status_code == 403
    assert client.get(reverse("portfolio-me")).status_code == 403


@pytest.mark.parametrize(
    "model,basename",
    [
        (Achievement, "achievement"),
        (AthleticResult, "athleticresult"),
        (HighlightVideo, "highlightvideo"),
        (SocialLink, "sociallink"),
    ],
)
def test_record_ownership(owner, demo, model, basename):
    record = model.objects.first()
    assert owner.get(reverse(basename + "-list")).data["results"] == []
    endpoint = reverse(basename + "-detail", args=[record.pk])
    assert owner.get(endpoint).status_code == 404
    assert owner.patch(endpoint, {"title": "hijacked"}, format="json").status_code == 404
    assert owner.delete(endpoint).status_code == 404
    assert model.objects.filter(pk=record.pk).exists()


def test_owner_can_crud_all_records(owner, demo, user):
    sport = Sport.objects.first()
    cases = [
        ("achievement", {"title": "My award"}),
        (
            "athleticresult",
            {
                "sport": str(sport.pk),
                "event": "Meet",
                "metric": "Time",
                "value": "12.5",
                "unit": "seconds",
                "date": "2026-01-01",
            },
        ),
        ("highlightvideo", {"title": "Clip", "url": "https://example.com/clip"}),
        ("sociallink", {"platform": "Website", "url": "https://example.com"}),
    ]
    for basename, data in cases:
        response = owner.post(
            reverse(basename + "-list"),
            {
                **data,
                "athlete": str(demo.athlete_profile.pk),
                "portfolio": str(demo.athlete_profile.portfolio.pk),
            },
            format="json",
        )
        assert response.status_code == 201, response.data
        endpoint = reverse(basename + "-detail", args=[response.data["id"]])
        assert owner.get(endpoint).status_code == 200
        assert owner.patch(endpoint, data, format="json").status_code == 200
        assert owner.delete(endpoint).status_code == 204
    assert demo.athlete_profile.achievements.count() == 1


def test_public_portfolio_privacy_publication_and_unpublication(client, demo):
    portfolio = demo.athlete_profile.portfolio
    endpoint = reverse("portfolio-public", args=[portfolio.slug])
    response = client.get(endpoint)
    assert response.status_code == 200 and response.data["completion_percentage"] == 100
    athlete = response.data["athlete"]
    assert athlete["achievements"] and athlete["results"] and athlete["highlights"]
    assert (
        not {"email", "phone_number", "date_of_birth", "gender", "user", "ncaa_id"} & athlete.keys()
    )
    assert not {"gpa", "ncaa_id"} & athlete["education"].keys()
    assert client.patch(endpoint, {"story": "attack"}, format="json").status_code == 405
    client.force_authenticate(demo)
    assert (
        client.patch(reverse("portfolio-me"), {"is_published": False}, format="json").status_code
        == 200
    )
    assert client.get(endpoint).status_code == 404
    assert client.get(reverse("portfolio-me")).status_code == 200
    assert (
        client.patch(reverse("portfolio-me"), {"is_published": True}, format="json").status_code
        == 200
    )
    assert client.get(endpoint).status_code == 200


def test_cannot_publish_incomplete_portfolio(owner):
    assert (
        owner.patch(reverse("portfolio-me"), {"is_published": True}, format="json").status_code
        == 400
    )
    response = owner.get(reverse("portfolio-me"))
    assert response.data["completion_percentage"] == 0
    assert (
        APIClient().get(reverse("portfolio-public", args=[response.data["slug"]])).status_code
        == 404
    )
    assert APIClient().get(reverse("portfolio-public", args=["missing"])).status_code == 404


def test_unique_slug_and_platform_and_safe_urls(owner, demo):
    assert (
        owner.patch(
            reverse("portfolio-me"), {"slug": demo.athlete_profile.portfolio.slug}, format="json"
        ).status_code
        == 400
    )
    endpoint = reverse("sociallink-list")
    assert (
        owner.post(
            endpoint, {"platform": "website", "url": "javascript:alert(1)"}, format="json"
        ).status_code
        == 400
    )
    assert (
        owner.post(
            endpoint, {"platform": "website", "url": "https://example.com"}, format="json"
        ).status_code
        == 201
    )
    assert (
        owner.post(
            endpoint, {"platform": "WEBSITE", "url": "https://example.com"}, format="json"
        ).status_code
        == 400
    )


def test_seed_idempotency_and_preserves_existing_edits(settings, demo):
    models = [
        User,
        AthleteProfile,
        AthleteSportProfile,
        Education,
        Portfolio,
        Sport,
        Position,
        Achievement,
        AthleticResult,
        HighlightVideo,
        SocialLink,
    ]
    before = [model.objects.count() for model in models]
    demo.full_name = "Edited Name"
    demo.set_password("Changed-secure-password!")
    demo.save()
    call_command("seed_demo", stdout=StringIO())
    assert before == [model.objects.count() for model in models]
    demo.refresh_from_db()
    assert demo.full_name == "Edited Name" and demo.check_password("Changed-secure-password!")
    assert demo.athlete_profile.portfolio.completion_percentage == 100


def test_seed_forbidden_in_production(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("seed_demo")
    assert not User.objects.exists()


def test_demo_login(client, demo):
    assert (
        client.post(
            reverse("token-obtain-pair"), {"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        ).status_code
        == 200
    )


def test_sports_catalog_filter(owner, demo):
    sport = Sport.objects.get(slug="basketball")
    response = owner.get(reverse("position-list"), {"sport": str(sport.pk)})
    assert response.status_code == 200 and response.data["count"] == 5
    assert all(item["sport"] == sport.pk for item in response.data["results"])
    assert owner.get(reverse("sport-detail", args=["basketball"])).status_code == 200


def test_health_failure_is_sanitized(client):
    with patch(
        "apps.common.views.connection.cursor", side_effect=DatabaseError("private connection info")
    ):
        response = client.get(reverse("health-check"))
    assert response.status_code == 503
    assert "private" not in response.content.decode()


def test_published_story_cannot_be_cleared(client, demo):
    client.force_authenticate(demo)
    assert client.patch(reverse("portfolio-me"), {"story": ""}, format="json").status_code == 400
    assert (
        client.patch(
            reverse("portfolio-me"), {"story": "", "is_published": False}, format="json"
        ).status_code
        == 200
    )


def test_disabled_athlete_is_not_public(client, demo):
    endpoint = reverse("portfolio-public", args=[demo.athlete_profile.portfolio.slug])
    demo.is_active = False
    demo.save()
    assert client.get(endpoint).status_code == 404
    assert (
        client.post(
            reverse("token-obtain-pair"), {"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        ).status_code
        == 401
    )


def test_seed_sports_works_in_production(settings):
    settings.DEBUG = False
    call_command("seed_sports", stdout=StringIO())
    call_command("seed_sports", stdout=StringIO())
    assert Sport.objects.count() == 5
    assert Position.objects.count() == 20
    assert not User.objects.exists()
