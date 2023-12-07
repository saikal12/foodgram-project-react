import logging

from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filter_is_favorited(self, queryset, name, value):
        logging.debug('start filter_is_favorited')
        user = self.request.user.id
        if value:
            logging.debug('filter for value')
            return queryset.filter(favorite__user__pk=user)
        else:
            return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        logging.debug('start filter_is_in_shopping_cart')
        user = self.request.user.id
        if value:
            logging.debug('filter for value')
            return queryset.filter(shoppingcart__user__pk=user)
        return queryset

