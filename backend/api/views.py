from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http.response import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from djoser.views import UserViewSet
from recipes.models import (CartRecipeModel, Favorites, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = ()
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = ()
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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[IsAuthenticated])
    def list_action(self, request, pk=None, model=None):
        if request.method == 'GET':
            return self.add_to_list(model, request.user, pk)
        if request.method == 'DELETE':
            return self.remove_from_list(model, request.user, pk)
        return None

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.list_action(request, pk=pk, model=Favorites)

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.list_action(request, pk=pk, model=CartRecipeModel)

    def construct_shopping_list(self, user, ingredients):
        today = timezone.now().date()
        shopping_list = (f'Список покупок для: {user.get_full_name()}\n\n'
                         f'Дата: {today:%Y-%m-%d}\n\n')
        shopping_list += '\n'.join([
            f'- {ingredient.ingredient.name}'
            f'-({ingredient.ingredient.measurement_unit})'
            f'- {ingredient.amount}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'
        return shopping_list

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response({'message': 'Shopping cart is empty.'})

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).select_related('recipe__shopping_cart__user', 'ingredient').values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        shopping_list = self.construct_shopping_list(user, ingredients)

        filename = f'{user.username}_shopping_list.txt'
        response = FileResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    def add_to_list(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return Response({'errors': 'Рецепт уже добавлен в список'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален'},
                        status=status.HTTP_400_BAD_REQUEST)


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
