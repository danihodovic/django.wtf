# pylint: disable=redefined-outer-name
import pytest
import responses
from pytest_factoryboy import register

from django_wtf.core.factories import (
    RepositoryFactory,
    RepositoryStarsFactory,
    ValidRepositoryFactory,
)
from django_wtf.users.models import User
from django_wtf.users.tests.factories import UserFactory

register(RepositoryFactory)
register(ValidRepositoryFactory)
register(RepositoryStarsFactory)


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):  # pylint: disable=redefined-outer-name
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
@pytest.mark.django_db
def user_client(client, user):
    """
    Creates an authenticated user client.
    """
    client.force_login(user)
    setattr(client, "user", user)
    return client
