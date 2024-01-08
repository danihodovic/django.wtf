import pytest
from allauth.account.models import EmailAddress
from django.contrib.messages import get_messages
from django.urls.base import reverse
from pytest_django.asserts import assertRedirects

from django_wtf.core.models import EmailSubscriber

url = reverse("core:subscriber-create")

pytestmark = pytest.mark.django_db


def test_create_email_subscriberview(user_client, mailoutbox):
    EmailAddress.objects.create(
        user=user_client.user, verified=True, primary=True, email="bob@gmail.com"
    )
    res = user_client.post(url, follow=True)

    assertRedirects(
        res,
        reverse("core:index"),
        status_code=302,
        target_status_code=200,
        fetch_redirect_response=True,
    )

    assert EmailSubscriber.objects.filter(user=user_client.user).count() == 1
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "Subscription confirmed to Django.WTF"
    assert mail.to == ["bob@gmail.com"]
    assert mail.body == "Woohoo"

    messages = list(get_messages(res.wsgi_request))
    assert (
        messages[0].message
        == "We will send you email updates every other week on trending repositories."
    )


def test_only_creates_one_subscriber(user_client):
    EmailAddress.objects.create(
        user=user_client.user, verified=True, primary=True, email="bob@gmail.com"
    )
    res = user_client.post(url, follow=True)
    assertRedirects(
        res,
        reverse("core:index"),
    )
    res = user_client.post(url, follow=True)
    assertRedirects(
        res,
        reverse("core:index"),
    )
    assert EmailSubscriber.objects.filter(user=user_client.user).count() == 1
