from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Follow


User = get_user_model()


class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "password", "email", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class UserFullSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        ]

    def to_representation(self, instance):
        if isinstance(instance, AnonymousUser):
            return {"detail": "Authentication credentials were not provided."}
        return super().to_representation(instance)

    def get_avatar(self, obj):
        request = self.context.get("request")
        if request and obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("user", "following")

    def validate(self, data):
        user = data["user"]
        following = data["following"]

        if user == following:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )

        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError("Вы уже подписаны.")

        return data
