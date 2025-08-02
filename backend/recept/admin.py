from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class AuthorFilter(AutocompleteFilter):
    title = 'Автор'
    field_name = 'author'


class TagFilter(AutocompleteFilter):
    title = 'Тег'
    field_name = 'tags'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    list_display_links = ['name', 'id']
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug',)
    list_display_links = ['slug', 'name', 'id']
    search_fields = ('name', 'slug')
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'cooking_time', 'get_favorites_count', 'id',
    )
    list_display_links = ['name', 'author']
    search_fields = ('name', 'author__username')
    list_filter = (TagFilter, AuthorFilter)
    autocomplete_fields = ['author', 'tags']
    inlines = (RecipeIngredientInline,)
    ordering = ('-id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related(
            'tags', 'ingredients', 'favorited_by'
        )

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()
    get_favorites_count.short_description = 'В избранном'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user',)
    list_display_links = ['recipe', 'id']
    list_filter = ('user',)
    autocomplete_fields = ['user', 'recipe']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ['id', 'user', 'recipe']
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
    autocomplete_fields = ['user', 'recipe']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')
