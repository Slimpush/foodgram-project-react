from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User
from .filters import IngredientFilter, RecipeFilter
from .paginators import PageLimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShoppingListSerializer,
                          SubscribeListSerializer, TagSerializer,
                          UserSerializer)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.process_request(Favorites, request.user, pk,
                                    FavoriteSerializer)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.process_request(ShoppingCart, request.user, pk,
                                    ShoppingListSerializer)

    def process_request(self, model, user, pk, serializer_class):
        if self.request.method == 'DELETE':
            get_object_or_404(model, user=user, recipe__id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {
            'user': user.id,
            'recipe': pk
        }
        serializer_instance = serializer_class(
            data=data,
            context={'request': self.request}
        )
        serializer_instance.is_valid(raise_exception=True)
        serializer_instance.save(user=user, recipe_id=pk)
        return Response(serializer_instance.data,
                        status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user
        file_name = f'{user.username}_shopping_list.txt'
        shopping_list = 'Список покупок:'

        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=F('amount')
        )
        shopping_list += '\n'.join([
            f"{ingredient['ingredient__name']} "
            f"({ingredient['ingredient__measurement_unit']}) - "
            f"{ingredient['amount']}"
            for ingredient in ingredients
        ])
        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        ShoppingCart.objects.filter(user=user).delete()
        return response


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        data = {
            'user': request.user.id,
            'author': id
        }
        serializer = FollowSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = request.user
        author = self.get_object()

        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = self.queryset.filter(following__user=user)
        page = self.paginate_queryset(queryset)

        serializer = SubscribeListSerializer(
            page,
            many=True,
            context={'request': request}
        )

        return self.get_paginated_response(serializer.data)
