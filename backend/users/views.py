from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from recept.serializers import SubscriptionSerializer
from users.serializers import AvatarSerializer

from .models import Follow


User = get_user_model()


class UserAvatarAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(DjoserUserViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ["list", "create"]:
            return [permission() for permission in [AllowAny]]
        return super().get_permissions()

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return super().me(request, *args, **kwargs)

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(followers__user=request.user).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        user = request.user

        if author == user:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Follow.objects.filter(user=user, following=author).exists():
            return Response(
                {"errors": "Вы уже подписаны."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=user, following=author)
        serializer = SubscriptionSerializer(
            author, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        follow = Follow.objects.filter(user=request.user, following=author)

        if not follow.exists():
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
