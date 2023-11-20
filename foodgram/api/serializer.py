import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from recipes.models import (Favorite, Follow, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator
from users.models import MyUser


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
        model = MyUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, author):
        request = self.context('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, author=author).exists()
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
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.PrimaryKeyRelatedField()

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
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients',
            'is_in_shopping_cart', 'is_favorited'

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
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = self.data.get('ingredients')
        tags = self.data.get('tags')
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

    def create_update_ingredients(self, ingredient_data, recipe):
        for ingredient in ingredient_data:
            ingredient_obj = get_object_or_404(
                Ingredient, pk=ingredient.get('id')
            )
            amount_data = ingredient.get('amount')
            IngredientInRecipe.objects.create(
                recipe=recipe, ingredient=ingredient_obj, amount=amount_data
            )

    def create_update_tags(self, tags_data, recipe):
        recipe.tags.set(tags_data)

    def create(self, validated_data):
        ingredient_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        self.create_update_ingredients(ingredient_data, recipe)
        self.create_update_tags(tags_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.image = validated_data.get('image')
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        ingredient_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
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


class ShortRecipeSerializer(ModelSerializer):
    """Дополнительный сериализатор для рецептов """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'cooking_time', 'image', 'name',)


class FollowSerializer(MyUserSerializer):
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )
    recipes = serializers.SerializerMethodField(
        read_only=True, method_name='get_recipes')

    class Meta(MyUserSerializer.Meta):
        fields = MyUserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipe_limit')
        if request.GET.get("recipe_limit"):
            recipes = obj.recipes.all()[:int(limit)]
        else:
            recipes = obj.recipes.all()
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
