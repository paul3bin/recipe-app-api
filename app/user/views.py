from rest_framework import generics
from . import serializers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings


class CreateUserView(generics.CreateAPIView):
    # Create a new user in the system
    serializer_class = serializers.UserSerializer


class CreateTokenView(ObtainAuthToken):
    # Create new auth token for user
    serializer_class = serializers.AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
