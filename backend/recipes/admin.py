from django.contrib import admin
from django.contrib.admin import display

from .models import (CartRecipeModel, Favorites, Ingredient,
                     Recipe, RecipeIngredient, Tag)


@admin.register(CartRecipeModel)
class CartRecipeModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Ingredient)
class IngredientAdmins(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorites_add',)
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'name', 'tags',)

    @display(description='Количество в избранных')
    def favorites_add(self, obj):
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug')
    list_filter = ('name', )
