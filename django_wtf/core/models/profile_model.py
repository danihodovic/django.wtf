# pylint: disable=import-outside-toplevel,too-few-public-methods
import logging
from datetime import datetime, timedelta

from cacheops import cached_as
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from model_utils.models import TimeStampedModel


class UserType(models.TextChoices):
    USER = ("User", "User")
    ORGANIZATION = ("Organization", "Organization")
    BOT = ("Bot", "Bot")


class ProfileContributesToValidProjectsManager(models.Manager):
    def get_queryset(self):
        from django_wtf.core.models.repository_model import Repository

        # If it has a category it's been manually categorized
        valid_repos = Repository.valid.all()
        return (
            super()
            .get_queryset()
            .filter(contributor__repository__in=valid_repos)
            .distinct()
        )


class Profile(TimeStampedModel):
    objects = models.Manager()
    contributes_to_valid_repos = ProfileContributesToValidProjectsManager()
    github_id = models.PositiveIntegerField()
    login = models.CharField(max_length=100, unique=True)
    type = models.CharField(
        max_length=30, choices=UserType.choices, null=True, blank=True
    )
    avatar_url = models.URLField()
    followers = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"<Profile: {self.login}>"

    @property
    def github_url(self):
        return f"https://github.com/{self.login}"

    def top_contributions(self):
        from django_wtf.core.models.contributor_model import Contributor

        @cached_as(Contributor, timeout=24 * 60 * 60)
        def _fn(self):
            return self.contributor_set.filter(contributions__gte=20).order_by(
                "-contributions"
            )

        return _fn(self)

    def followers_since(self, td: timedelta, date=None):
        if date is None:
            date = datetime.today().date()
        previous_date = date - td
        try:
            previous_followers = ProfileFollowers.objects.get(
                created_at=previous_date, profile=self
            )
        except ObjectDoesNotExist:
            logging.debug(f"ProfileFollowers at {previous_date=} does not exist")
            return 0
        assert self.followers
        return self.followers - previous_followers.followers


class ProfileFollowers(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    created_at = models.DateField()
    followers = models.PositiveIntegerField()

    class Meta:
        unique_together = (
            "profile",
            "created_at",
        )

    def __str__(self):
        return f"<ProfileFollowers {self.profile.login} at {self.created_at}>"
