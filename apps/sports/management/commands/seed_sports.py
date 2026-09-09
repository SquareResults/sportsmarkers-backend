from django.core.management.base import BaseCommand
from django.db import transaction

from apps.sports.models import Position, Sport


class Command(BaseCommand):
    help = "Idempotently create the MVP sports catalog; safe in production."

    @transaction.atomic
    def handle(self, *args, **options):
        catalog = {
            "Basketball": [
                "Point Guard",
                "Shooting Guard",
                "Small Forward",
                "Power Forward",
                "Center",
            ],
            "Soccer": ["Goalkeeper", "Defender", "Midfielder", "Forward"],
            "Football": ["Quarterback", "Running Back", "Wide Receiver", "Linebacker"],
            "Volleyball": ["Setter", "Outside Hitter", "Libero"],
            "Track and Field": ["Sprinter", "Distance Runner", "Jumper", "Thrower"],
        }
        for name, positions in catalog.items():
            sport, _ = Sport.objects.get_or_create(
                name=name, defaults={"slug": name.lower().replace(" ", "-")}
            )
            for position in positions:
                Position.objects.get_or_create(sport=sport, name=position)
        self.stdout.write(self.style.SUCCESS("Sports catalog ready."))
