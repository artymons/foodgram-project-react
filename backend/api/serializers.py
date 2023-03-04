import re

from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction

from recipes.models import (CustomUser, Favorite, Ingredient,
                            IngredientInRecipe, Recipe, ShoppingList, Tag)
from users.models import Follow


class BaseUserSerializer(serializers.ModelSerializer):
    """
    Пользователи.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'password', 'first_name', 'last_name'
        )


class TagSerializer(serializers.ModelSerializer):
    """
    Теги.
    """
    class Meta:
        model = Tag
        fields = '__all__'

    def validate_hex_color(self, data):
        color = self.initial_data.get('hex_color')
        match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
        if not match:
            raise serializers.ValidationError('некорректный hex')

        return data


class IngredientSerializer(serializers.ModelSerializer):
    """
    Ингредиенты.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    """
    Подписчики.
    """
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author'],
                message=('Подписка уже осуществлена')
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShowFollowersSerializer(
            instance.author,
            context=context).data


class FavorShopGeneralSerializer(serializers.ModelSerializer):
    """
    Общий сериализатор для наследования избранного и списка покупок.
    """
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShowRecipeSerializer(
            instance.recipe,
            context=context).data


class FavoriteSerializer(FavorShopGeneralSerializer):
    """
    Избранное.
    """
    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message=('Рецепт уже добавлен в избранное')
            )
        ]


class ShoppingListSerializer(FavorShopGeneralSerializer):
    """
    Список покупок.
    """
    class Meta:
        model = ShoppingList
        fields = (
            'user',
            'recipe'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=['user', 'recipe'],
                message=('Продукты уже в корзине')
            )
        ]


class ListRecipeSerializer(serializers.ModelSerializer):
    """
    Отображение списка рецептов.
    """
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    author = BaseUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return ShoppingList.objects.filter(recipe=obj, user=user).exists()

    def get_ingredients(self, obj):
        qs = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializerToCreateRecipe(qs, many=True).data


class ShowRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецепта в избраном и списке покупок.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_ingredients(self, obj):
        qs = obj.recipes_ingredients_list.all()
        return IngredientInRecipeSerializer(qs, many=True).data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения ингредиентов внутри рецепта(полный список).
    """

    class Meta:
        model = IngredientInRecipe
        fields = '__all__'


class IngredientInRecipeSerializerToCreateRecipe(serializers.ModelSerializer):
    """
    Сериализатор для отображения ингридиента в - Список рецептов.
    """
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        read_only=True
    )
    name = serializers.SlugRelatedField(
        source='ingredient',
        read_only=True,
        slug_field='name'
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient',
        read_only=True,
        slug_field='measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class ShowFollowerRecipeSerializer(serializers.ModelSerializer):
    """
    Рецепт в выдаче - мои подписки.
    """
    image = serializers.ImageField(
        max_length=None,
        required=True,
        allow_empty_file=False,
        use_url=True,
    )

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShowFollowersSerializer(BaseUserSerializer):
    """
    Выдача - мои подписки.
    """
    recipes = ShowFollowerRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField('count_author_recipes')

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def count_author_recipes(self, user):
        return user.recipes.count()


class AddIngredientToRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добовления созданых ингредиентов в рецепт.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Создание и обновление данных по рецепту.
    """
    image = Base64ImageField(max_length=None, use_url=True)
    author = BaseUserSerializer(read_only=True)
    ingredients = AddIngredientToRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['tags', 'ingredients',
                        'name', 'image', 'text', 'cooking_time'],
            )
        ]

    def create_ingredients(self, recipe, ingredients_data):
        print(ingredients_data)
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.save()
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients_data)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        instance.tags.set(tags_data)
        return instance

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = []
        for ingredient_item in ingredients:
            if ingredient_item['id'] in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': (
                        'Повторяются'
                    )
                })
            ingredients_list.append(ingredient_item['id'])

            if int(ingredient_item['amount']) <= 0:
                raise serializers.ValidationError({
                    'ingredients': (
                        'Количество ингридиента должно быть больше нуля!'
                    )
                })
        return data

    def to_representation(self, instance):
        return ListRecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data
