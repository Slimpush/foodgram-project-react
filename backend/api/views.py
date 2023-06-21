from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http.response import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from djoser.views import UserViewSet
from recipes.models import (CartRecipeModel, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .paginators import PageLimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          ShortRecipeSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)

User = get_user_model()


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, )
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPagination
    filter_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]

    @action(detail=True, methods=['get', 'post', 'delete'],
            permission_classes=[IsAuthenticated])
    def cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            cart_recipe, created = CartRecipeModel.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response({'errors': 'Рецепт уже добавлен в корзину.'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            cart_recipe = get_object_or_404(
                CartRecipeModel, user=user, recipe=recipe
            )
            cart_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            cart_recipes = user.shopping_cart.filter(recipe=recipe)
            if not cart_recipes.exists():
                return Response({'errors': 'Рецепт отсутствует в корзине.'},
                                status=status.HTTP_404_NOT_FOUND)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def shopping_cart(self, request):
        user = request.user
        cart_recipes = user.shopping_cart.select_related('recipe')
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=[cart.recipe for cart in cart_recipes]
        ).select_related('ingredient').values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = timezone.now().date()
        shopping_list = (f'Список покупок для: {user.get_full_name()}\n\n'
                         f'Дата: {today:%Y-%m-%d}\n\n')
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]}'
            f'-({ingredient["ingredient__measurement_unit"]})'
            f'- {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = FileResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        serializer = SubscribeSerializer(
            author, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        Follow.objects.get_or_create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = self.queryset.filter(following__user=user)
        page = self.paginate_queryset(queryset)

        serializer = SubscribeSerializer(
            page,
            many=True,
            context={'request': request}
        )

        return self.get_paginated_response(serializer.data)
