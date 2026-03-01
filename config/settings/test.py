"""
With these settings, tests run faster.
"""

# pylint: disable=wildcard-import,unused-wildcard-import
from django_o11y.logging.setup import build_logging_dict

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="1rp5jTWPOJxopl8y0CQaCqNgdixcPCU3SZUusboAl51iRVlaYVxBC4yep9pSGC8H",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DJANGO_O11Y = {
    **DJANGO_O11Y,  # noqa: F405
    "TRACING": {"ENABLED": False},
    "LOGGING": {
        "LEVEL": "WARNING",
        "FILE_ENABLED": False,
    },
    "METRICS": {
        "PROMETHEUS_ENABLED": False,
        "EXPORT_MIGRATIONS": False,
    },
    "CELERY": {"ENABLED": False},
    "PROFILING": {"ENABLED": False},
}

LOGGING = build_logging_dict(extra=EXTRA_LOGGING)  # noqa: F405

# Your stuff...
# ------------------------------------------------------------------------------
