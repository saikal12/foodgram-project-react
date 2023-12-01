from django.db.models import Sum, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializer import (FavoriteSerializer, IngredientSerializer,
                            RecipeCreateSerializer, RecipeReadSerializer,
                            ShoppingCartSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from .utils import to_pdf


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для обработки запросов, связанных с рецептами."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe_id=OuterRef('id'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe_id=OuterRef('id')
                    )
                )
            )
            return queryset
        return queryset

    def get_serializer_class(self):
        """Метод для вызова определенного сериализатора. """
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def to_post(self, serializer, request, pk):
        """Метод для добавления."""
        user = request.user
        data = {
            'user': user.id,
            'recipe': pk
        }
        favorite = serializer(data=data)
        favorite.is_valid(raise_exception=True)
        favorite.save()
        return Response(favorite.data, status=status.HTTP_201_CREATED)

    def to_delete(self, request, model, pk):
        """Метод для удаления."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'DELETE':
            obj = model.objects.filter(user=user, recipe=recipe)
            delete = obj.delete()
            if delete[0] > 0:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite'
    )
    def favorite(self, request, pk):
        model = Favorite
        if request.method == 'POST':
            return self.to_post(
                pk=pk, serializer=FavoriteSerializer,
                request=request
            )
        return self.to_delete(pk=pk, model=model, request=request)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        if request.method == 'POST':
            return self.to_post(
                pk=pk, serializer=ShoppingCartSerializer,
                request=request
            )
        return self.to_delete(pk=pk, model=model, request=request)

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
        ingredients = (IngredientInRecipe.objects.filter(
            recipe__shoppingcart__user_id=request.user.id
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount')).
                       order_by('ingredient__name'))
        return to_pdf(ingredients=ingredients)



class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для обработки запросов, связанных с тегом."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для обработки запросов, связанных с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
