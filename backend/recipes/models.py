from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator

User = get_user_model()


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
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
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
        validators=[MinValueValidator
                    (1, 'Блюдо не может приготовиться меньше чем за 1 минуту')]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
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
        validators=[MinValueValidator
                    (1, 'Блюдо должно содержать хотя бы 1 ингредиент')
                    ],
    )

    class Meta:
        ordering = ('recipe', )
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique ingredients recipe'
                                    )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} ({self.ingredient.measurement_unit})'
            f' - {self.amount} '
        )


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='favorites',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='n_favorites',
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique favorite recipe')
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class CartRecipeModel(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='cart',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='if_cart',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique shopping cart')
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в Корзину покупок'
