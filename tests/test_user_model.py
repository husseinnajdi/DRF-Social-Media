import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

User = get_user_model()


@pytest.mark.django_db
def test_create_user_defaults():
    user = User.objects.create_user(
        email="Test@Example.com", username="test", password="pass12345!"
    )
    assert user.email == "test@example.com"
    assert user.role == "user"
    assert user.status == "active"
    assert user.check_password("pass12345!")


@pytest.mark.django_db
def test_create_superuser_is_admin():
    admin = User.objects.create_superuser(
        email="admin@example.com", username="admin", password="pass12345!"
    )
    assert admin.role == "admin"
    assert admin.is_staff and admin.is_superuser


def test_email_must_be_unique():
    User.objects.create_user(
        email="a@example.com",
        username="a",
        password="x12345678!",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email="a@example.com",
            username="b",
            password="x12345678!",
        )


def test_email_uniqueness_is_case_insensitive():
    User.objects.create_user(
        email="a@example.com",
        username="a",
        password="x12345678!",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email="A@Example.com",
            username="b",
            password="x12345678!",
        )
