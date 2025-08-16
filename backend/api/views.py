from django.db.models import Count, Exists, OuterRef, Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .mixins import CollectionActionMixin, SubscriptionActionMixin
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(DjoserUserViewSet, SubscriptionActionMixin):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        """Определяет необходимые разрешения в зависимости от действия."""
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        user = request.user
        subscriptions = User.objects.filter(subscribers__user=user).annotate(
            recipes_count=Count('recipes')
        )
        page = self.paginate_queryset(subscriptions)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Позволяет подписаться/отписаться от автора."""
        return self.handle_subscription_action(
            request=request,
            user_id=id,
            model_class=Subscription,
            serializer_class=SubscriptionSerializer
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        """Изменяет пароль текущего пользователя."""
        user = request.user
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Устанавливает или удаляет аватар пользователя."""
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Обязательное поле.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SetAvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами (только чтение)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet, CollectionActionMixin):
    """ViewSet для полной работы с рецептами."""

    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)

    def get_queryset(self):
        """Возвращает базовый QuerySet с оптимизацией запросов."""
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            Prefetch(
                'recipe_ingredients',
                queryset=RecipeIngredient.objects.select_related('ingredient')
            )
        )

        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )

        return queryset

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт в избранное."""
        return self.handle_collection_action(
            request=request,
            pk=pk,
            model_class=Favorite,
            serializer_class=FavoriteSerializer,
            error_exists='Рецепт уже в избранном',
            error_not_found='Рецепт не в избранном'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт в список покупок."""
        return self.handle_collection_action(
            request=request,
            pk=pk,
            model_class=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            error_exists='Рецепт уже в списке покупок',
            error_not_found='Рецепт не в списке покупок'
        )

    def _create_shopping_list_content(self, user):
        """Создает содержимое списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart_by__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = [
            'Список покупок\n\n'
        ]

        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            shopping_list.append(f'{name} ({unit}) — {amount}\n')

        return ''.join(shopping_list)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивает список покупок пользователя в формате txt."""
        user = request.user
        content = self._create_shopping_list_content(user)

        response = HttpResponse(
            content=content,
            content_type='text/plain'
        )
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.txt"'
                                           )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = f'{request.scheme}://{request.get_host()}/s/{recipe.id}'
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
