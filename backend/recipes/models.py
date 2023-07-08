from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 721
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 50


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=settings.MAX_LEN_RECIPE_FIELD
    )
    color = models.CharField(
        verbose_name='Цветовой код',
        unique=True,
        max_length=settings.MAX_LEN_HEX,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Корректно введите цвет в HEX-кодировке',
            )
        ]
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        unique=True,
        max_length=settings.MAX_LEN_RECIPE_FIELD,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=settings.MAX_LEN_RECIPE_FIELD,
        db_index=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=settings.MAX_LEN_RECIPE_FIELD,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=('name', 'measurement_unit'),
                                    name='unique ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=settings.MAX_LEN_RECIPE_FIELD,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    text = models.TextField('Описание рецепта')
    image = models.ImageField(
        verbose_name='Фото рецепта',
        upload_to='recipes/'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='RecipeIngredient'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            MIN_COOKING_TIME,
            message='Время приготовления не менее 1 минуты!'
        ), MaxValueValidator(
            MAX_COOKING_TIME,
            message='Время приготовления не более 12 часов!'
        )]
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}. Автор: {self.author.username}'


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredient_list',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиентов',
        validators=[MinValueValidator(
            MIN_INGREDIENT_AMOUNT,
            'Блюдо должно содержать хотя бы 1 ингредиент'
        ), MaxValueValidator(
            MAX_INGREDIENT_AMOUNT,
            'Рецепт слишком сложный'
        )],
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(fields=('ingredient', 'recipe'),
                                    name='unique ingredients recipe'
                                    )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} ({self.ingredient.measurement_unit})'
            f' - {self.amount} '
        )


class CartFavorites(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_unique_cart_favorites'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в {self._meta.verbose_name}'

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.Meta.default_related_name = cls.__name__.lower()


class Favorites(CartFavorites):

    class Meta(CartFavorites.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(CartFavorites):

    class Meta(CartFavorites.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
