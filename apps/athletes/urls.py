from django.urls import path

from .views import EducationView, OnboardingSummaryView, PersonalView, SportProfileView

urlpatterns = [
    path("me/", PersonalView.as_view(), name="athlete-me"),
    path("me/sport/", SportProfileView.as_view(), name="athlete-sport"),
    path("me/education/", EducationView.as_view(), name="athlete-education"),
    path("me/onboarding/", OnboardingSummaryView.as_view(), name="athlete-onboarding"),
]
