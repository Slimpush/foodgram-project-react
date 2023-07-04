from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .paginators import PageLimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          ShoppingListSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ('name', )
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    pagination_class = PageLimitPagination
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to(Favorites, request.user, pk,
                               FavoriteSerializer())
        else:
            return self.delete_from(Favorites, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to(ShoppingCart, request.user, pk,
                               ShoppingListSerializer())
        else:
            return self.delete_from(ShoppingCart, request.user, pk)

    def add_to(self, model, user, pk, serializer):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)

        serialized_data = serializer.data
        return Response(serialized_data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        purchases = ShoppingCart.objects.filter(user=user)
        file_name = f'{user.username}_shopping_list.txt'
        shopping_list = 'Список покупок:'

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

    def get_instance(self):
        return self.request.user

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

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

    @action(
        ['POST'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        update_session_auth_hash(self.request, self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
