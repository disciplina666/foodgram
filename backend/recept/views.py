from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
from django.contrib.auth import get_user_model
from rest_framework import filters, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import Recipe, Tag, Ingredient, ShoppingCart, Favorite, RecipeIngredient
from .serializers import (
    RecipeReadSerializer, RecipeWriteSerializer,
    TagSerializer, IngredientSerializer,
    RecipeShortSerializer
)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__id=author)

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1':
            if user.is_authenticated:
                queryset = queryset.filter(favorited_by__user=user)
            else:
                return Recipe.objects.none()

        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1':
            if user.is_authenticated:
                queryset = queryset.filter(shopping_cart__user=user)
            else:
                return Recipe.objects.none()

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

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в избранном.'}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({'errors': 'Рецепт не в избранном.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в корзине.'}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if cart_item.exists():
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({'errors': 'Рецепт не в корзине.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_name='get-link', url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_name='download_shopping_cart', url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
            )
            .annotate(total=Sum('amount'))
            .order_by('name')
        )

        lines = [
            f"{item['name']} ({item['unit']}) {item['total']}"
            for item in ingredients
        ]
        content = '\n'.join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset.distinct()