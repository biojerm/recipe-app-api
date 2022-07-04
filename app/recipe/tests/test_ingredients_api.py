
from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


def create_user(**params):
    return get_user_model().objects.create_user(**params)


@pytest.fixture
def user():
    """A sample user for testing"""
    new_user = create_user(
        email='test@user.com',
        password='testspass',
        name='name',
    )
    return new_user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_api_client(user):
    """An api client with a logged in user"""
    client = APIClient()
    client.force_authenticate(user)
    return client


INGREDIENT_URL = reverse('recipe:ingredient-list')


class TestPublicIngredientApi:
    """Test the publicly available ingredients API"""

    def test_login_required(self, api_client):
        """Test that login is required to reach this endpoint"""
        res = api_client.get(INGREDIENT_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateIngredientApi:
    """Test the private ingredients api"""

    @pytest.mark.django_db
    def test_retrieve_ingredient_list(self, user, user_api_client):
        """Test retrieve ingredent list"""
        Ingredient.objects.create(user=user, name='Kale')
        Ingredient.objects.create(user=user, name='Salt')

        res = user_api_client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_ingredients_limited_to_user(self, user, user_api_client):
        """Test that only the authenticated user's ingredients returned"""
        user2 = create_user(
            email='user2@myapp.com', password='password', name='person2')
        Ingredient.objects.create(user=user2, name='Milk')

        ingredient = Ingredient.objects.create(user=user, name='Eggs')
        res = user_api_client.get(INGREDIENT_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]['name'] == ingredient.name

    @pytest.mark.django_db
    def test_create_ingredient_successful(self, user, user_api_client):
        """Test create a new ingredient"""
        payload = {'name': 'Cabbage'}
        user_api_client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=user,
            name=payload['name']
        ).exists()
        assert exists

    @pytest.mark.django_db
    def test_create_ingredient_invalid(self, user_api_client):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        res = user_api_client.post(INGREDIENT_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_retrieve_ingredients_assigned_to_recipes(
        self, user, user_api_client
    ):
        """Test filtering ingredient by those assgned to recipes"""
        ingredient1 = Ingredient.objects.create(user=user, name="apples")
        ingredient2 = Ingredient.objects.create(user=user, name="Turkey")

        recipe=Recipe.objects.create(
            title="apple crumble",
            time_minutes=5,
            price=10,
            user=user
        )

        recipe.ingredients.add(ingredient1)
        res = user_api_client.get(INGREDIENT_URL, {'assigned_only':1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    @pytest.mark.django_db
    def test_retrieve_ingredients_assigned_unique(self, user, user_api_client):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient= Ingredient.objects.create(user=user, name='Eggs')
        Ingredient.objects.create(user=user, name='Cheese')

        recipe1 = Recipe.objects.create(
            title="poached eggs",
            time_minutes=5,
            price=1,
            user=user
        )

        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title="scrambled eggs",
            time_minutes=5,
            price=1,
            user=user
        )
        recipe2.ingredients.add(ingredient)

        res = user_api_client.get(INGREDIENT_URL, {"assigned_only":1})

        assert len(res.data) == 1