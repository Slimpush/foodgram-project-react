from django.contrib import admin
from django.contrib.admin import display

from .models import (CartRecipeModel, Favorites, Ingredient, Recipe,
                     RecipeIngredient, Tag)


class CartRecipeModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'count_favorites',)
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'name', 'tags',)

    @display(description='Количество рецептов в избранном')
    def count_favorites(self, obj):
        return obj.favorites.count()


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug')
    list_filter = ('name', )


admin.site.register(CartRecipeModel, CartRecipeModelAdmin)
admin.site.register(Favorites, FavoritesAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Tag, TagAdmin)
