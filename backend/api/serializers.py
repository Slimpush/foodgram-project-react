from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (ModelSerializer, ReadOnlyField,
                                        SerializerMethodField)
from users.models import Follow, User


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class ShortRecipeSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name', )

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Follow.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Нельзя подписаться повторно',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class RecipeIngredientSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')
    amount = SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )

    def get_amount(self, obj):
        return obj.amount


class RecipeSerializer(ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredient_list',
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'tags',
            'author',
            'ingredients',
            'name',
            'text',
            'cooking_time',
        )


class RecipeCreateSerializer(ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()

    def get_ingredients(self, obj):
        ingredient_data = RecipeIngredient.objects.filter(recipe=obj)
        serializer = RecipeIngredientSerializer(ingredient_data, many=True)
        return serializer.data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'tags',
            'author',
            'ingredients',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredient_list = []
        for ingredient_item in ingredients:
            print(ingredient_item)
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredient_list:
                raise ValidationError('Нужны уникальные ингредиенты!')
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 0:
                raise ValidationError({
                    ('Количество ингредиентов должно быть больше 1')
                })
            if not ingredients:
                raise ValidationError(
                    'Блюдо должно содержать хотя бы 1 ингредиент')
        data['ingredients'] = ingredients
        return data

    @staticmethod
    def create_ingredients(instance, ingredients_data):
        ingredient_list = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            amount = ingredient_data.get('amount')
            recipe_ingredient = RecipeIngredient(
                ingredient=ingredient,
                amount=amount,
                recipe=instance,
            )
            ingredient_list.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        if not self.is_valid():
            raise ValidationError('Validation error')
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = self.initial_data.get('tags')
        request = self.context['request']
        author = request.user
        recipe = Recipe.objects.create(image=image,
                                       author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = self.initial_data.get('tags')
        instance.tags.set(tags)

        RecipeIngredient.objects.filter(recipe=instance).delete()

        ingredients_data = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        abstract = True
        fields = ('user', 'recipe')


class FavoriteSerializer(FavoriteCartSerializer):
    class Meta(FavoriteCartSerializer.Meta):
        model = Favorites
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в избранном',
            )
        ]

    def create(self, validated_data):
        return self.Meta.model.objects.create(
            user=self.context.get('request').user, **validated_data
        )


class ShoppingListSerializer(FavoriteCartSerializer):

    class Meta(FavoriteCartSerializer.Meta):
        model = ShoppingCart
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в корзине покупок'
            )
        ]

    def create(self, validated_data):
        return self.Meta.model.objects.create(
            user=self.context.get('request').user, **validated_data
        )
