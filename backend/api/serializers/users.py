from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import Follow


User = get_user_model()


class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password',
                        'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserFullSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name',
                        'last_name', 'is_subscribed', 'avatar']

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or user.is_anonymous:
            return False

        return Follow.objects.filter(user=user, following=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('following',)

    def validate(self, data):
        user = self.context['request'].user
        following = data['following']

        if user == following:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')

        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError('Вы уже подписаны.')

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        return Follow.objects.create(user=user, **validated_data)
