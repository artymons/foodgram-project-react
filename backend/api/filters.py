from django_filters import rest_framework as filter
from recipes.models import Recipe, Tag


class RecipeFilter(filter.FilterSet):
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug'
    )
    is_favorited = filter.BooleanFilter(method='get_favorite')
    is_in_shopping_cart = filter.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def get_favorite(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(favorite_recipes__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(customers__user=user)
        return queryset
