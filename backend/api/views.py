from datetime import date

import django_filters.rest_framework
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from recipes.models import (CustomUser, Favorite, Ingredient,
                            IngredientInRecipe, Recipe, ShoppingList, Tag)
from rest_framework import filters, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Follow

from .filters import RecipeFilter
from .paginators import PageNumberPaginatorModified
from .permissions import AdminOrAuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientSerializer,
                          ListRecipeSerializer, ShoppingListSerializer,
                          ShowFollowersSerializer, TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filter_class = RecipeFilter
    pagination_class = PageNumberPaginatorModified
    permission_classes = [AdminOrAuthorOrReadOnly, ]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ListRecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', ]


@api_view(['GET', ])
@permission_classes([IsAuthenticated])
def showfollows(request):
    user_obj = CustomUser.objects.filter(following__user=request.user)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(user_obj, request)
    serializer = ShowFollowersSerializer(
        result_page, many=True, context={'current_user': request.user})
    return paginator.get_paginated_response(serializer.data)


class FollowView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, author_id):
        user = request.user

        data = {
            'user': user.id,
            'author': author_id
        }
        serializer = FollowSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, author_id):
        user = request.user
        author = get_object_or_404(CustomUser, id=author_id)
        obj = get_object_or_404(Follow, user=user, author=author)
        obj.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class FavouriteView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, recipe_id):
        user = request.user
        data = {
            'user': user.id,
            'recipe': recipe_id,
        }
        serializer = FavoriteSerializer(
            data=data,
            context={'request': request}
        )

        if not serializer.is_valid():
            Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        obj = get_object_or_404(Favorite, user=user, recipe=recipe)
        obj.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class ShoppingListView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, recipe_id):
        user = request.user
        data = {
            'user': user.id,
            'recipe': recipe_id,
        }

        context = {'request': request}
        serializer = ShoppingListSerializer(data=data, context=context)

        if not serializer.is_valid():
            Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        else:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        obj = get_object_or_404(ShoppingList, user=user, recipe=recipe)
        obj.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class DownloadShoppingCart(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__customers__user=user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(total=Sum('amount'))
        wishlist = '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["total"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        today = date.today()
        wishlist_basement = (f'\nFoodGram, {today.year}')
        result = wishlist + wishlist_basement
        filename = 'wishlist.txt'
        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
