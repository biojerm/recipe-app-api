
from django.contrib.auth import get_user_model

from core import models

import pytest


def sample_user(email='test@myapp.com', password='testpass'):
    """create a sample user"""
    return get_user_model().objects.create_user(email, password)


class TestModel():

    @pytest.mark.django_db
    def test_creat_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""

        email = 'testemail@fake.com'
        password = 'password123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        assert user.email == email
        assert user.check_password(password)

    @pytest.mark.django_db
    def test_new_user_email_normalized(self):
        """Tests the email for a new users is normalized"""
        email = 'testemail@FAKE.COM'
        user = get_user_model().objects.create_user(email, 'password')

        assert user.email == email.lower()

    @pytest.mark.django_db
    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with pytest.raises(ValueError):
            get_user_model().objects.create_user(None, 'password')

    @pytest.mark.django_db
    def test_create_new_super_user(self):
        """Test creating new super user"""
        email = 'staff@fake.com'
        user = get_user_model().objects.create_superuser(email, 'password')

        assert user.is_superuser
        assert user.is_staff

    @pytest.mark.django_db
    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan',
        )

        assert str(tag) == tag.name

    @pytest.mark.django_db
    def test_ingredient_str(self):
        """Test the tag string representation"""
        ingredients = models.Ingredient.objects.create(
            user=sample_user(),
            name='Cucumber'
        )
        assert str(ingredients) == ingredients.name

    @pytest.mark.django_db
    def test_recipe_str(self):
        """Test teh recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title="Steak and Mushroom sauce",
            time_minutes=5,
            price=5.00
        )

        assert str(recipe) == recipe.title
