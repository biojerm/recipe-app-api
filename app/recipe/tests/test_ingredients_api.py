
from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

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



