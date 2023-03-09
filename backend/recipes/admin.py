from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     ShoppingList, Tag, IngredientInRecipe)
from users.models import Follow


class RecipeAdmin(admin.ModelAdmin):
    list_filter = ('author', 'name', 'tags')
    list_display = ('name', 'author', 'followers', 'id')

    def followers(self, obj):
        return obj.favorite_recipes.all().count()
    followers.short_description = 'В избранном'


class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name', )
    list_display = ('name', 'measurement_unit')


admin.site.register(Follow)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
admin.site.register(IngredientInRecipe)