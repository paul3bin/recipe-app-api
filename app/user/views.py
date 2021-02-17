from rest_framework import generics, authentication, permissions
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


class ManageUserView(generics.RetrieveUpdateAPIView):
    # Manage the authenticated user
    serializer_class = serializers.UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        # retrieve and return authenticated user
        return self.request.user
