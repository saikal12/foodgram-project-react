
from django.contrib.admin import ModelAdmin, register

from .models import *


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author', 'id', 'count_favorite')
    list_filter = ('author', 'tags', 'name')
    search_fields = ('name', 'tags',)

    def count_favorite(self, obj):
        return obj.favorites.count()

    count_favorite.short_description = (
        'Количество добавлений рецепта в избранное'
    )


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')


@register(IngredientInRecipe)
class IngredientInRecipeAdmin(ModelAdmin):
    list_display = ('id', 'ingredient', 'recipe', 'amount')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@register(ShoppingCart)
class ShoppingCart(ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
