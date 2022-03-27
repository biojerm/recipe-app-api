from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest
from pytest_django.asserts import assertContains


@pytest.fixture
def user(admin_client):
    user = get_user_model().objects.create_user(
        email='test@fake.com',
        password='password123',
        name='Test user full name'
    )
    yield user


class TestAdminSite:

    @pytest.mark.django_db
    def test_users_listed(self, admin_client, user):
        """Test that users are listed on user page"""

        url = reverse("admin:core_user_changelist")
        res = admin_client.get(url)

        assertContains(res, user.name)
        assertContains(res, user.email)

    def test_user_change_page(self, admin_client, user):
        """Test the user edit page works"""
        url = reverse('admin:core_user_change', args=[user.id])
        res = admin_client.get(url)
        assert res.status_code == 200

    def test_create_user_page(self, admin_client):
        """Test that the create user page works"""
        url = reverse('admin:core_user_add')
        res = admin_client.get(url)
        assert res.status_code == 200
