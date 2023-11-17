from api1.filters import IngredientFilter, RecipeFilter
from api1.pagination import CustomPagination
from api1.permissions import IsOwnerOrReadOnly
from api1.serializer import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, ShortRecipeSerializer,
                             TagSerializer)
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

FILE_NAME = "shopping-list.txt"


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для обработки запросов, связанных с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
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
        """Метод для вызова удаления или публикации. """
        user = self.request.user
        recipe = self.get_object()
        if request.method == 'DELETE':
            obj = model.objects.filter(user=user, recipe=recipe)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.method == 'POST':
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
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite'
    )
    def favorite(self, request, pk):
        model = Favorite
        return self.to_post_delete(pk=pk, model=model, request=request)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        return self.to_post_delete(pk=pk, model=model, request=request)

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
            recipe__shopping_cart__user_id=request.user.id
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={FILE_NAME}'
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
        c = canvas.Canvas(response)
        c.setFont('DejaVu', 17)
        WIDTH = 60
        HEIGHT = 770
        c.drawString(WIDTH, HEIGHT, "  Ингредиенты: ")
        for new_string in ingredients:
            HEIGHT -= 30
            name = new_string['ingredient__name']
            measurement_unit = new_string['ingredient__measurement_unit']
            amount = new_string['sum']
            string = f'{name}  -  {amount}({measurement_unit})'
            c.drawString(WIDTH, HEIGHT, string)
        c.showPage()
        c.save()
        return response


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
