from django.contrib import admin

from .models import AthleteSportProfile, Position, Sport

admin.site.register(Sport)
admin.site.register(Position)
admin.site.register(AthleteSportProfile)
