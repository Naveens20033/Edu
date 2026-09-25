"""Authentication endpoints for login, refresh, logout, and profile."""
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import LoginTokenSerializer, UserSerializer

class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginTokenSerializer


class RefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutSerializer(serializers.Serializer):
    """Accept a refresh token without rotating it as the refresh endpoint does."""
    refresh = serializers.CharField()


class LogoutView(APIView):
    # Possession of the refresh token is the authority to revoke it. This also
    # lets logout work when the short-lived access token has already expired.
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            refresh.blacklist()
        except TokenError:
            return Response({"detail": "Refresh token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)
