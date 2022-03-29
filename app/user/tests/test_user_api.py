from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


@pytest.fixture
def api_client():
    return APIClient()


class TestPublicUserAPITests:
    """Test the users API (public)"""

    @pytest.mark.django_db
    def test_create_valid_user_success(self, api_client):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': "test@fake.com",
            'password': 'testpass',
            'name': 'Test name'
        }
        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(**res.data)
        assert user.check_password(payload['password'])
        assert 'password' not in res.data

    @pytest.mark.django_db
    def test_user_exists(self, api_client):
        """Test creating a user that already exists fails"""
        payload = {
            'email': 'test@fake.com',
            'password': 'testpass',
            'name': 'test'}
        create_user(**payload)

        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_passwords_are_too_short(self, api_client):
        """Test password more than 5 characters"""
        payload = {
            'email': 'test@fake.com',
            'password': 'pw',
            'name': 'test'}
        res = api_client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        assert not user_exists
