from django.db import transaction

from apps.education.models import Education
from apps.portfolios.models import Portfolio
from apps.sports.models import AthleteSportProfile

from .models import AthleteProfile


@transaction.atomic
def ensure_athlete(user):
    athlete, _ = AthleteProfile.objects.get_or_create(user=user)
    AthleteSportProfile.objects.get_or_create(athlete=athlete)
    Education.objects.get_or_create(athlete=athlete)
    Portfolio.objects.get_or_create(athlete=athlete)
    return athlete


def completed_sections(athlete):
    sport = getattr(athlete, "sport_profile", None)
    education = getattr(athlete, "education", None)
    return {
        "personal": bool(
            athlete.date_of_birth and athlete.city and athlete.state and athlete.gender
        ),
        "sport": bool(
            sport
            and sport.primary_sport_id
            and sport.positions.exists()
            and sport.height_cm
            and sport.weight_kg
            and sport.years_played is not None
        ),
        "education": bool(education and education.school and education.graduation_year),
    }


def onboarding_summary(athlete):
    sections = completed_sections(athlete)
    completed = [key for key, value in sections.items() if value]
    missing = [key for key, value in sections.items() if not value]
    status = "completed" if not missing else "in_progress" if completed else "not_started"
    step = list(sections).index(missing[0]) if missing else 3
    AthleteProfile.objects.filter(pk=athlete.pk).update(
        onboarding_status=status, onboarding_step=step
    )
    athlete.onboarding_status, athlete.onboarding_step = status, step
    return {
        "completed_sections": completed,
        "missing_sections": missing,
        "onboarding_status": status,
        "onboarding_step": step,
        "completion_percentage": round(len(completed) / 3 * 100),
    }
