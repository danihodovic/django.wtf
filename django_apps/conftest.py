import pytest
import responses

from django_apps.users.models import User
from django_apps.users.tests.factories import UserFactory


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
