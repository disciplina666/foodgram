from django.db import models
from django.contrib.auth import get_user_model

from .constants import MAX_NAME_LENGTH

User = get_user_model()


class Ingredient(models.Model):
    '''Модель ингридентов.'''
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Единица измерения')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    '''Модель тегов.'''
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, verbose_name='Название тега')
    slug = models.SlugField(unique=True, verbose_name='SLUG')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''Модель рецепта.'''
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes', verbose_name='Автор')
    name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Название')
    image = models.ImageField(upload_to='recipes', verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, related_name='recipes', verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления (в минутах)')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_links'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_links'
    )
    amount = models.DecimalField(decimal_places=2, max_digits=10)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='<UNK>')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )