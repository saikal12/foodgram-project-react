from django.db import models
from django.db.models import Exists, OuterRef

from recipes.models import Favorite, ShoppingCart


class RecipeManager(models.Manager):
    def add_annotations(self, user):
        queryset = self.get_queryset.annotate(
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
