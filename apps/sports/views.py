from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from .models import Position, Sport
from .serializers import PositionSerializer, SportSerializer


@extend_schema(tags=["Sports"])
class SportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sport.objects.prefetch_related("positions").all()
    serializer_class = SportSerializer
    lookup_field = "slug"


@extend_schema(tags=["Sports"])
class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Position.objects.select_related("sport").all()
    serializer_class = PositionSerializer
    filterset_fields = ["sport"]
