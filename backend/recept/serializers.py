from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import Follow
from users.serializers import UserFullSerializer

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.FloatField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть не менее 1.')
        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserFullSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(allow_null=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        ]

    def get_ingredients(self, obj):
        links = obj.ingredient_links.select_related('ingredient')
        return RecipeIngredientReadSerializer(links, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and obj.shopping_cart.filter(
            user=user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time']

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент.')
        unique_ingredients = set()
        for item in value:
            if item['id'] in unique_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            unique_ingredients.add(item['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Картинка обязательна.')
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть >= 1.')
        return value

    def update_recipe_data(self, recipe, ingredients, tags):
        recipe.tags.set(tags)
        recipe.ingredient_links.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe, ingredient=item['id'], amount=item['amount'])
            for item in ingredients
        ])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data.pop('author', None)
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        self.update_recipe_data(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        request = self.context['request']
        if instance.author != request.user:
            raise serializers.ValidationError(
                'Вы не можете изменить чужой рецепт.')

        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': 'Поле обязательно.'})
        if tags is None:
            raise serializers.ValidationError({'tags': 'Поле обязательно.'})

        instance = super().update(instance, validated_data)

        self.update_recipe_data(instance, ingredients, tags)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def validate(self, data):
        if Favorite.objects.filter(
                user=data['user'], recipe=data['recipe']).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return data

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def validate(self, data):
        if ShoppingCart.objects.filter(
                user=data['user'], recipe=data['recipe']).exists():
            raise serializers.ValidationError('Рецепт уже в корзине.')
        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'recipes', 'recipes_count', 'is_subscribed'
        ]

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user is None or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if request:
            limit = request.query_params.get('recipes_limit')
            if limit and limit.isdigit():
                recipes = recipes[: int(limit)]
        return RecipeShortSerializer(
            recipes, many=True, context=self.context).data
