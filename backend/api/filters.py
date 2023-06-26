from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag
from rest_framework.filters import SearchFilter


class IngredientFilter(SearchFilter):
    search_parameters = 'name'

    class Meta:
        model = Ingredient
        field = ('name', )


class RecipeFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name',
    )
    author = filters.CharFilter(
        field_name='author',
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    bookmarked = filters.BooleanFilter(method='filter_bookmarked')
    purchased = filters.BooleanFilter(method='filter_purchased')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'bookmarked', 'purchased',)

    def filter_bookmarked(self, queryset, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_purchased(self, queryset, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
