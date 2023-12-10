from django.core.validators import (
    MinValueValidator, RegexValidator, MaxValueValidator
)
from django.db import models
from django.conf import settings
from django.db.models import Exists, OuterRef

from users.models import User


class AnnotationsManager(models.Manager):
    def add_annotations(self, user):
        queryset = self.get_queryset().annotate(
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


class Ingredient(models.Model):
    """Модель для описания ингредиента"""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=settings.NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=settings.NAME_MAX_LENGTH,
    )

    class Meta:
        ordering = ('name', 'measurement_unit')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_measurement_unit_and_name'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель для описания тега"""
    name = models.CharField(
        verbose_name='Название тега',
        max_length=settings.NAME_MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        max_length=settings.SLUG_MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=settings.COLOR_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введенное значение не является цветом в формате HEX!'
            )
        ],
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для описания рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=settings.NAME_MAX_LENGTH,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    image = models.ImageField(
        verbose_name='Фотография рецепта',
        upload_to='recipes_images/'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                settings.MIN_VALUE,
                message='Минимальное значение 1 минута!'
            ),
            MaxValueValidator(
                settings.MAX_VALUE,
                message='Максимальное значение 32767 минут!'
            )
        ],
        verbose_name='Время приготовления (в минутах)'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Список ингредиентов',
        related_name='recipes',
    )
    objects = AnnotationsManager()

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель для связи рецепта и ингредиента"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='in_recipe',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_list',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                settings.MIN_VALUE,
                message='Минимальное количество 1!'
            ),
            MaxValueValidator(
                settings.MAX_VALUE,
                message='Максимальное значение 32767 минут!'
            )
        ],
        verbose_name='Количество ингредиента'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients_in_the_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


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

    class Meta:
        abstract = True


class Favorite(BaseModel):
    """Модель для избранных рецептов"""
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class ShoppingCart(BaseModel):
    """Модель для корзины покупок """
    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_shopping_cart'
            )
        ]

