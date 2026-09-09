from django.db import models

from apps.common.models import TimeStampedModel


class Achievement(TimeStampedModel):
    athlete = models.ForeignKey(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="achievements"
    )
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, max_length=3000)

    class Meta:
        ordering = ["-date", "id"]

    def __str__(self):
        return self.title


class AthleticResult(TimeStampedModel):
    athlete = models.ForeignKey(
        "athletes.AthleteProfile", on_delete=models.CASCADE, related_name="results"
    )
    sport = models.ForeignKey("sports.Sport", on_delete=models.PROTECT)
    event = models.CharField(max_length=200)
    metric = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=30)
    date = models.DateField()

    class Meta:
        ordering = ["-date", "id"]

    def __str__(self):
        return f"{self.event}: {self.metric}"
