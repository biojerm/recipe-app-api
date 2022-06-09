from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

from rest_framework import status
from rest_framework.test import APIClient


from core.models import Recipe, Tag, Ingredient


from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_tag(sample_user, name="Main course"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=sample_user, name=name)


def sample_ingredient(sample_user, name='Cinnamon'):
    """create and return a sample ingredient"""
    return Ingredient.objects.create(user=sample_user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }

    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


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


class TestPublicRecipeApi:
    """Test unauthenticated recipe API access"""

    def test_auth_required(self, api_client):
        res = api_client.get(RECIPES_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateRecipeAPI:
    """Test unauthenticated recipe API access"""

    @pytest.mark.django_db
    def test_retrieve_recipes(self, user, user_api_client):
        """Test retrieving a list of recipes"""
        sample_recipe(user=user)
        sample_recipe(user=user)

        res = user_api_client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_recipies_limited_to_user(self, user, user_api_client):
        user2 = create_user(
            email='user2@myapp.com', password='password', name='person2')

        sample_recipe(user=user2)
        sample_recipe(user=user)
        res = user_api_client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=user)
        serializer = RecipeSerializer(recipes, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_view_recipe_detail(self, user, user_api_client):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=user)
        recipe.tags.add(sample_tag(sample_user=user))
        recipe.ingredients.add(sample_ingredient(sample_user=user))

        url = detail_url(recipe.id)
        res = user_api_client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        assert res.data == serializer.data
