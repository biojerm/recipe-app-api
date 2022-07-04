from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


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


TAGS_URL = reverse('recipe:tag-list')


class TestPublicTagsApi:
    """Test the pulicly available tags API"""

    def test_login_requried(self, api_client):
        """Test that login is requrired for retrieving tags"""
        res = api_client.get(TAGS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateTagsApi:
    """Test the authorized user tags API"""
    @pytest.mark.django_db
    def test_retrieve_tags(self, user, user_api_client):
        """Test retrieving tags"""
        Tag.objects.create(user=user, name='Vegan')
        Tag.objects.create(user=user, name='Dessert')

        res = user_api_client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_tags_limited_to_user(self, user, user_api_client):
        """Test that tags returns are for the authenticated_user"""
        user2 = create_user(
            email='user2@myapp.com', password='password', name='person2')

        Tag.objects.create(user=user2, name="Fruity")

        tag = Tag.objects.create(user=user, name="Comfort Food")
        res = user_api_client.get(TAGS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]['name'] == tag.name

    @pytest.mark.django_db
    def test_create_tag_successful(self, user, user_api_client):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        user_api_client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=user,
            name=payload['name']
        ).exists()

        assert exists

    @pytest.mark.django_db
    def test_create_tag_with_invalid(self, user_api_client):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = user_api_client.post(TAGS_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_retrieve_tags_assigned_to_recipes(self, user, user_api_client):
        """Test filtering tags bythose assigned to recipes"""
        tag1 = Tag.objects.create(user=user, name='Breakfast')
        tag2 = Tag.objects.create(user=user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Toast',
            time_minutes=10,
            price=5.00,
            user=user
        )
        recipe.tags.add(tag1)

        res = user_api_client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    @pytest.mark.django_db
    def test_retrieve_tags_assinged_unique(self, user, user_api_client):
        """Test filtering tags assigned returns unique items"""
        tag = Tag.objects.create(user=user, name='Breakfast')
        Tag.objects.create(user=user, name='Lunch')

        recipe1 = Recipe.objects.create(
            title='Pandcakes',
            time_minutes=5,
            price=3.00,
            user=user
        )

        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Porrage',
            time_minutes=3,
            price=2.00,
            user=user
        )
        recipe2.tags.add(tag)

        res = user_api_client.get(TAGS_URL, {'assigned_only': 1})

        assert len(res.data) == 1
