from django.db import models

from apps.common.models import TimeStampedModel


class HighlightVideo(TimeStampedModel):
    athlete = models.ForeignKey(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="highlights"
    )
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True, max_length=3000)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return self.title
