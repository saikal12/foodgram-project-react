from django.urls import path, include
from rest_framework import routers

from api1.views import RecipeViewSet, TagViewSet, IngredientViewSet

app_name = 'api1'

router = routers.DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
]