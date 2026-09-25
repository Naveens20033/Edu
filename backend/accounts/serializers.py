"""Authentication payloads and the safe current-user representation."""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")
        read_only_fields = fields


class LoginTokenSerializer(TokenObtainPairSerializer):
    """Issue standard JWTs and return the signed-in profile alongside them."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.get_username()
        return token

    def validate(self, attrs):
        identity = attrs.get(self.username_field, "").strip()
        if "@" in identity:
            user_model = get_user_model()
            username = user_model.objects.filter(email__iexact=identity).values_list("username", flat=True).first()
            # Let Simple JWT return its ordinary generic credential error if
            # no account matches; never reveal whether the email is registered.
            attrs[self.username_field] = username or identity
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
