import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    """Сериализатор декодирования картинки."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, author):
        request = self.context['request']
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=author
            ).exists()
        return False


class TagSerializer(ModelSerializer):
    """Сериализатор для вывода тэгов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeCreateSerializer(ModelSerializer):
    """Сериализатор для проверки количество ингрединта в рецепте"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=1, max_value=32767
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('amount', 'id')


class IngredientInRecipeSerializer(ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('name', 'id', 'amount', 'measurement_unit')


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для вывода рецепта."""
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_list', many=True
    )
    author = UserSerializer(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False, read_only=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'text', 'image',
            'cooking_time', 'tags', 'ingredients',
            'is_in_shopping_cart', 'is_favorited', 'name',
            'author'
        )


class RecipeCreateSerializer(ModelSerializer):
    """Сериализатор для создания рецептов"""
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент!'
            })
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            ingredient_list.append(ingredient_id)
            if len(ingredients) != len(set(ingredient_list)):
                raise ValidationError({
                    'ingredients': 'Ингридиенты не должны повторяться!'
                })
        if not tags:
            raise ValidationError({
                'tags': 'Нужен хотя бы один тег!'
            })
        tags_set = set(tags)
        if len(tags) != len(tags_set):
            raise ValidationError({
                'tags': 'Теги должны быть уникальными!'
            })
        return data

    def validate_image(self, value):
        if not value:
            raise ValidationError(
                'Поле "image" должно быть заполнено'
            )
        return value

    @staticmethod
    def create_update_ingredients(ingredient_data, recipe):
        ingredient_create = []
        for ingredient in ingredient_data:
            ingredient_obj = ingredient.get('id')
            amount_data = ingredient.get('amount')
            new_ingredient = IngredientInRecipe(
                recipe=recipe, ingredient=ingredient_obj, amount=amount_data
            )
            ingredient_create.append(new_ingredient)
            IngredientInRecipe.objects.bulk_create(ingredient_create)

    @staticmethod
    def create_update_tags(tags_data, recipe):
        recipe.tags.set(tags_data)

    @transaction.atomic
    def create(self, validated_data):
        ingredient_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        request = self.context.get('request')
        author = request.user
        recipe = Recipe.objects.create(
            author=author, **validated_data
        )
        self.create_update_ingredients(ingredient_data, recipe)
        self.create_update_tags(tags_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredient_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.clear()
        self.create_update_ingredients(ingredient_data, instance)
        self.create_update_tags(tags_data, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance,
                                    context=context).data


class FavoriteSerializer(ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""
    class Meta:
        model = Favorite
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже есть в Вашем списке.'
            )
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['recipe'] = ShortRecipeSerializer(instance.recipe).data
        return data


class ShoppingCartSerializer(ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже есть в Вашем списке покупок.'
            )
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['recipe'] = ShortRecipeSerializer(instance.recipe).data
        return data



class ShortRecipeSerializer(ModelSerializer):
    """Дополнительный сериализатор для рецептов """
    class Meta:
        model = Recipe
        fields = ('id', 'cooking_time', 'image', 'name',)


class FollowSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )
    recipes = serializers.SerializerMethodField(
        read_only=True, method_name='get_recipes')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipe_limit')
        recipes = obj.recipes.all()
        if request.GET.get('recipe_limit'):
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class FollowCreateSerializer(ModelSerializer):
    """Сериализатор для создания подписки на автора."""
    class Meta:
        model = Follow
        fields = '__all__'

    validators = [
        UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=('user', 'author'),
            message='Вы уже подписаны на этого пользователя.'
        )
    ]

    def validate(self, data):
        if data['author'] == data['user']:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя.'
            )
        return data
