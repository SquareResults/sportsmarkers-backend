import uuid

from django.db import models

from apps.common.models import TimeStampedModel


def public_slug():
    return uuid.uuid4().hex


class Portfolio(TimeStampedModel):
    athlete = models.OneToOneField(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="portfolio"
    )
    slug = models.SlugField(max_length=100, unique=True, default=public_slug)
    is_published = models.BooleanField(default=False, db_index=True)
    story = models.TextField(blank=True, max_length=10000)
    recruiting_status = models.CharField(
        max_length=20,
        default="open",
        choices=[
            ("open", "Open to opportunities"),
            ("committed", "Committed"),
            ("not_recruiting", "Not recruiting"),
        ],
    )
    goals = models.TextField(blank=True, max_length=5000)

    @property
    def completion_percentage(self):
        from apps.athletes.services import completed_sections

        sections = completed_sections(self.athlete)
        checks = list(sections.values()) + [
            bool(self.story and self.goals),
            self.athlete.achievements.exists(),
            self.athlete.results.exists(),
            self.social_links.exists(),
            self.athlete.highlights.exists(),
        ]
        return round(100 * sum(checks) / len(checks))

    def __str__(self):
        return self.slug


class SocialLink(TimeStampedModel):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="social_links")
    platform = models.CharField(max_length=50)
    url = models.URLField(max_length=500)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "platform"], name="unique_portfolio_platform"
            )
        ]

    def __str__(self):
        return self.platform
