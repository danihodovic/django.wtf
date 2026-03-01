from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return bool(getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True))

    def send_verification_code_sms(self, user, phone: str, code: str, **kwargs):
        return None

    def set_phone(self, user, phone: str, verified: bool):
        return None

    def get_phone(self, user):
        return None

    def set_phone_verified(self, user, phone: str):
        return None

    def get_user_by_phone(self, phone: str):
        return None


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return bool(getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True))
