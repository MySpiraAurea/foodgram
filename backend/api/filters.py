from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по наличию рецепта в избранном."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по наличию рецепта в списке покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shoppingcart_by__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов."""

    name = filters.CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
