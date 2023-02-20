import logging
import sys
import traceback

from django.conf import settings
from django.core.signals import got_request_exception
from django.dispatch import receiver
from mattermostdriver import Driver
from requests.exceptions import InvalidURL


# Add a listener to the got_caught_exception signal
# pylint: disable=unused-argument
@receiver(got_request_exception)
def send_exception_to_mattermost(sender, request, **kwargs):
    logging.info("Attempting to send request exception to Mattermost")
    client = mattermost_client()

    if not client:
        return

    _, exc_value, exc_traceback = sys.exc_info()
    if exc_value:
        message = f"Exception occurred: {exc_value}\n\nStack trace:\n{''.join(traceback.format_tb(exc_traceback))}"
        client.posts.create_post(
            options=dict(channel_id=settings.MATTERMOST_CHANNEL_ID, message=message)
        )


def mattermost_client():
    url = settings.MATTERMOST_URL.geturl()
    client = Driver(
        {
            "url": settings.MATTERMOST_URL.hostname,
            "port": 443,
            "token": settings.MATTERMOST_TOKEN,
        }
    )
    try:
        client.login()
        return client
    except InvalidURL:
        logging.exception(f"Invalid url configured for Mattermost {url=}")
    except ConnectionError:
        logging.exception("Error when trying to connect to the Mattermost server")
