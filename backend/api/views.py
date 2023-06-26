from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import (CartRecipeModel, Favorites, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .paginators import PageLimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, SubscribeSerializer, TagSerializer,
                          UserSerializer)

User = get_user_model()


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
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

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateSerializer

    def object_already_in_list(self, user, recipe, model):
        if model.objects.filter(user=user, recipe=recipe).exists():
            return True
        return False

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if not self.object_already_in_list(user, recipe, Favorites):
                Favorites.objects.create(user=user, recipe=recipe)
                serializer = SubscribeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_200_OK)
            text = {'errors': 'Объект уже в списке.'}
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            if self.object_already_in_list(user, recipe, Favorites):
                Favorites.objects.filter(user=user, recipe=recipe).delete()
                return Response(status=status.HTTP_200_OK)
            text = {'errors': 'Объект не в списке.'}
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        return Response(text, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if not self.object_already_in_list(user, recipe, CartRecipeModel):
                CartRecipeModel.objects.create(user=user, recipe=recipe)
                serializer = SubscribeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_200_OK)
            text = {'errors': 'Объект уже в списке.'}
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            if self.object_already_in_list(user, recipe, CartRecipeModel):
                CartRecipeModel.objects.filter(user=user,
                                               recipe=recipe).delete()
                return Response(status=status.HTTP_200_OK)
            text = {'errors': 'Объект не в списке.'}
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        return Response(text, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        purchases = CartRecipeModel.objects.filter(user=user)
        file_name = f'{user.username}_shopping_list.txt'
        shopping_list = 'Список покупок:\n\n'
        for purchase in purchases:
            ingredients = RecipeIngredient.objects.filter(
                recipe=purchase.recipe.id
            )
            for r in ingredients:
                i = r.ingredient
                line = f'{i.name} ({i.measurement_unit}) - {r.amount}'
                shopping_list += f'- {line}\n'
        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
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
