from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count', 'pub_date')
    list_display_links = ('name',)
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Оптимизирует запросы, предварительно загружая связанные объекты."""
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related(
            'tags',
            'recipe_ingredients__ingredient'
        ).annotate(favorites_count=Count('favorite_by'))

    def favorites_count(self, obj):
        return obj.favorites_count

    favorites_count.short_description = 'В избранном'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user',)
    list_filter = ('user',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user',)
    list_filter = ('user',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_display_links = ('recipe',)
    search_fields = ('recipe__name', 'ingredient__name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipe', 'ingredient'
        )
