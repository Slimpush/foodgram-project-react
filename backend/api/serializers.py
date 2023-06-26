from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
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
            'password',
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

        read_only_fields = (
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
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = ReadOnlyField(source='ingredients.name')
    measurement_unit = ReadOnlyField(source='ingredients.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


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
        fields = '__all__'


class RecipeCreateSerializer(ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='ingredient_list')
    get_user_item_relation = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = (
            "get_user_item_relation",
        )

    def get_ingredients(self, recipe):
        return recipe.ingredients.values(
            "id", "name", "measurement_unit", amount=F("recipe__amount")
        )

    def get_user_item_relation(self, recipe, relation_type):
        user = self.context.get("view").request.user
        if user.is_anonymous:
            return False

        relations = {
            "favorites": user.favorites,
            "carts": user.carts,
        }

        return relations[relation_type].filter(recipe=recipe).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Блюдо должно содержать хотя бы 1 ингредиент!'}
            )

        ingredient_ids = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_ids:
                raise ValidationError('Ингредиенты не могут повторяться!')
            ingredient_ids.append(ingredient_id)

            ingredient_amount = int(ingredient['amount'])
            if ingredient_amount < 1:
                raise ValidationError(
                    {'amount': 'Количество ингредиентов должно быть больше 1!'}
                )

        data['ingredients'] = ingredients
        return data

    @transaction.atomic
    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            ingredient_obj, _ = Ingredient.objects.get_or_create(
                name=ingredient['name'])
            RecipeIngredient.objects.create(
                ingredient=ingredient_obj,
                recipe=recipe,
                amount=ingredient['amount']
            )

    @transaction.atomic
    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = self.initial_data.get('tags')

        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags_data)

        self.create_ingredients(ingredients_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        if 'tags' in validated_data:
            instance.tags.set(validated_data['tags'])
        if 'ingredients' in validated_data:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients(validated_data['ingredients'], instance)

        instance.save()

        return instance
