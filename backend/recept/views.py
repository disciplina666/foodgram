from django.contrib.auth import get_user_model
from django.db.models import Exists, F, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.permissions import IsAuthorOrReadOnly

from .filters import RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related(
            'author').prefetch_related('tags', 'ingredients')
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk'))
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        recipe = self.get_object()
        if self.request.user != recipe.author:
            raise PermissionDenied('Вы не можете изменить чужой рецепт.')
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            raise PermissionDenied('Вы не можете удалить чужой рецепт.')
        instance.delete()

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(
                data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeShortSerializer(
                    recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted_count, _ = Favorite.objects.filter(
                user=user, recipe=recipe).delete()
            if deleted_count == 0:
                return Response({'errors': 'Рецепт не был в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = ShoppingCartSerializer(
                data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeShortSerializer(
                    recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted_count, _ = ShoppingCart.objects.filter(
                user=user, recipe=recipe).delete()
            if deleted_count == 0:
                return Response({'errors': 'Рецепт не был в корзине.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'],
            url_name='get-link', url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=user)
            .values(name=F('ingredient__name'), unit=F(
                'ingredient__measurement_unit'))
            .annotate(total=Sum('amount'))
            .order_by('name')
        )

        content = self.shopping_data(ingredients)
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    def shopping_data(self, ingredients):
        return '\n'.join(
            f"{item['name']} ({item['unit']}) {item['total']}"
            for item in ingredients
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset.distinct()
