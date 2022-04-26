from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


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

    @pytest.mark.django_db
    def test_create_token_for_user(self, api_client):
        """Test that a token is created for the user"""
        payload = {'email': 'test@myappdev.com', "password": "test"}
        create_user(**payload)
        res = api_client.post(TOKEN_URL, payload)

        assert 'token' in res.data
        assert res.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_create_token_invalid_credentials(self, api_client):
        """Test that a token is not created if invalid credentials given"""
        create_user(**{'email': 'test@myappdev.com', "password": "test"})
        payload = {'email': 'test@myappdev.com', "password": "wrong"}
        res = api_client.post(TOKEN_URL, **payload)

        assert 'token' not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_token_no_user(self, api_client):
        """Test that a token is not created if user does not exist"""
        payload = {'email': 'test@myappdev.com', "password": "test_pass"}
        res = api_client.post(TOKEN_URL, payload)

        assert 'token'not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_token_missing_field(self, api_client):
        """Test that email and password fields are required"""
        res = api_client.post(
            TOKEN_URL, {'email': 'test@myappdev.com', "password": ""}
        )

        assert 'token'not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_retrieve_user_unauthorized(self, api_client):
        """Test that authentication is required for users"""
        res = api_client.get(ME_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateUserApi:
    """Test API requetst that require authenication"""

    @pytest.mark.django_db
    def test_retrieve_profile_success(self, user_api_client, user):
        """Test retrieving profile for logged in used"""
        res = user_api_client.get(ME_URL)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == {
            "name": user.name,
            "email": user.email
        }

    @pytest.mark.django_db
    def test_post_me_not_allowed(self, user_api_client):
        """Test that post is note allowed on the ME_URL"""
        res = user_api_client.post(ME_URL, {})
        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_update_user_profile(self, user_api_client, user):
        """Test that post is note allowed on the ME_URL"""
        payload = {
            'name': 'new_name', 'password': "newpass"
        }
        res = user_api_client.patch(ME_URL, payload)
        user.refresh_from_db()

        assert user.name == payload['name']
        assert user.check_password(payload['password'])
        assert res.status_code == status.HTTP_200_OK
