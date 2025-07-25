from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from django.core.files.base import ContentFile

from drf_extra_fields.fields import Base64ImageField

from .models import Follow

User = get_user_model()

class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user

class UserFullSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_subscribed', 'avatar']

    def to_representation(self, instance):
        if isinstance(instance, AnonymousUser):
            return {'detail': 'Authentication credentials were not provided.'}
        return super().to_representation(instance)

    def get_avatar(self, obj):
        request = self.context.get('request')
        if request and obj.avatar and hasattr(obj.avatar, 'url'):
            try:
                return request.build_absolute_uri(obj.avatar.url)
            except Exception:
                return None
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)



