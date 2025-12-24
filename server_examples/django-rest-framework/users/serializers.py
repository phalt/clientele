from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active"]


class UserRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]
