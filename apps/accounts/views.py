from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserSerializer


@extend_schema(tags=["Authentication"])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


@extend_schema(tags=["Authentication"])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
