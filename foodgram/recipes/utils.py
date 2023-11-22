from django.db import models

from recipes.models import Recipe, User


class BaseModel(models.Model):
    """Абстрактная модель"""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='%(class)s',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='%(class)s',
        on_delete=models.CASCADE,
    )
