import pytest
import responses
from rest_framework.test import APIClient

from django_apps.users.models import User
from django_apps.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):  # pylint: disable=redefined-outer-name
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def create_user_client(db):
    def fn(client_cls=APIClient, login=True):
        user = UserFactory()
        client = client_cls()
        if login:
            client.force_login(user)
            setattr(client, "user", user)
        return client

    return fn


@pytest.fixture
def user_client(create_user_client):
    return create_user_client()
