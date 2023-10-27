from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from api1.pagination import CustomPagination
from api1.permissions import IsOwnerOrReadOnly

from api1.serializer import RecipeSerializer, RecipeCreateSerializer, FavoriteSerializer, \
    ShortRecipeSerializer, ShoppingCartSerializer, TagSerializer, IngredientSerializer
from recipes.models import *


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для обработки запросов, связанных с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Метод для вызова определенного сериализатора. """
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        elif self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer

    def to_post_delete(self, pk, model, request):
        user = self.request.user
        recipe = self.get_object()
        if request.methods == 'DELETE':
            obj = model.objects.filter(user=user, recipe=recipe)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.methods == 'POST':
            data = {
                'user': user.id,
                'recipe': pk
            }
            favorite = self.get_serializer(data=data)
            favorite.is_valid(raise_exception=True)
            favorite.save()
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=('IsAuthenticated',),
        url_path='favorite',
        url_name='favorite'
    )
    def favorite(self, request, pk):
        model = Favorite
        return self.to_post_delete(pk=pk, model=model, request=request)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=('IsAuthenticated',),
        url_path='shopping_cart',
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        return self.to_post_delete(pk=pk, model=model, request=request)

#подкорректировать
    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки"""

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list
    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
                 для выбранных рецептов"""
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_recipe__user = request.user
        ).values(
            'ingredient__name',
            'ingredient_measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilter,)
    search_fields = ('^name', 'name')
