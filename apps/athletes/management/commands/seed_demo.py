from datetime import date

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.athletes.services import ensure_athlete, onboarding_summary
from apps.careers.models import Achievement, AthleticResult
from apps.media_library.models import HighlightVideo
from apps.portfolios.models import SocialLink
from apps.sports.models import Position, Sport

DEMO_EMAIL = "demo.athlete@example.com"
DEMO_PASSWORD = "Development-Demo-2026!"


class Command(BaseCommand):
    help = "Seed sports and a complete fictional athlete (development only)."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "The demo uses public development credentials and requires DEBUG=True."
            )
        call_command("seed_sports", stdout=self.stdout)
        user, created = User.objects.get_or_create(
            email=DEMO_EMAIL, defaults={"full_name": "Jordan Taylor"}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        # Never reset an existing account's password or overwrite user-edited demo content.
        athlete = ensure_athlete(user)
        if created:
            athlete.date_of_birth = date(2008, 4, 12)
            athlete.city, athlete.state = "Phoenix", "Arizona"
            athlete.gender = "undisclosed"
            athlete.current_team = "Desert Valley Eagles (fictional)"
            athlete.biography = (
                "Fictional student-athlete passionate about teamwork and basketball."
            )
            athlete.profile_photo_url = "https://placehold.co/400x400.png?text=Demo+Athlete"
            athlete.phone_number = "+1-202-555-0147"
            athlete.save()
            sport = Sport.objects.get(slug="basketball")
            profile = athlete.sport_profile
            profile.primary_sport = sport
            profile.jersey_number, profile.height_cm, profile.weight_kg, profile.years_played = (
                "12",
                183,
                75,
                6,
            )
            profile.save()
            profile.positions.set([Position.objects.get(sport=sport, name="Point Guard")])
            education = athlete.education
            education.school = "Desert Valley High School (fictional)"
            education.graduation_year, education.gpa = 2027, "3.80"
            education.intended_major, education.ncaa_id = "Sports Science", "DEMO-ONLY"
            education.save()
            Achievement.objects.create(
                athlete=athlete,
                title="All-Region First Team",
                organization="Fictional Regional League",
                date=date(2026, 3, 15),
                description="Demonstration achievement, not verified.",
            )
            AthleticResult.objects.create(
                athlete=athlete,
                sport=sport,
                event="Demo season",
                metric="Points per game",
                value="18.5",
                unit="points",
                date=date(2026, 3, 15),
            )
            HighlightVideo.objects.create(
                athlete=athlete,
                title="Demo highlight placeholder",
                url="https://www.youtube.com/watch?v=aqz-KE-bpKQ",
                description="Sample video; replace with an athlete highlight before sharing.",
            )
            portfolio = athlete.portfolio
            portfolio.slug, portfolio.story = (
                "jordan-taylor-demo",
                "I lead through preparation, teamwork, and consistent effort. "
                "This is a fictional demo portfolio.",
            )
            portfolio.goals, portfolio.is_published = (
                "Study sports science and compete in college basketball.",
                True,
            )
            portfolio.save()
            SocialLink.objects.create(
                portfolio=portfolio, platform="website", url="https://example.com/jordan-demo"
            )
        onboarding_summary(athlete)
        self.stdout.write(
            self.style.SUCCESS(
                "Sports catalog and demo athlete ready. Existing demo data preserved."
            )
        )
