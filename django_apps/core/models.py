from datetime import datetime, timedelta

from cacheops import cached_as
from django.contrib.postgres.fields import ArrayField
from django.db import models
from model_utils.models import TimeStampedModel


class UserType(models.TextChoices):
    USER = ("User", "User")
    ORGANIZATION = ("Organization", "Organization")
    BOT = ("Bot", "Bot")


class RepositoryType(models.TextChoices):
    PROJECT = ("project", "project")
    APP = ("app", "app")


class Profile(TimeStampedModel):
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
        @cached_as(Contributor, timeout=24 * 60 * 60)
        def _fn(self):
            return self.contributor_set.filter(contributions__gt=20).order_by(
                "-contributions"
            )

        return _fn(self)


class Category(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=5)

    def __str__(self):
        return f"<Category: {self.name}>"


class Repository(TimeStampedModel):
    github_id = models.PositiveIntegerField()
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="repositories",
        related_query_name="repository",
    )
    categories = models.ManyToManyField(Category)
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100, unique=True)
    forks = models.PositiveIntegerField()
    open_issues = models.PositiveIntegerField()
    watchers = models.PositiveIntegerField()
    stars = models.PositiveIntegerField()
    archived = models.BooleanField(null=True)
    description = models.CharField(max_length=600, null=True)
    topics = ArrayField(models.CharField(max_length=50), null=True)
    type = models.CharField(
        max_length=30, choices=RepositoryType.choices, null=True, blank=True
    )

    @property
    def github_url(self):
        return f"https://github.com/{self.full_name}"

    def __repr__(self):
        return f"<Repository: {self.full_name}>"

    def __str__(self):
        return self.__repr__()

    def stars_since(self, td: timedelta, date=None):
        if date is None:
            date = datetime.today().date()
        previous_date = date - td
        previous_stars = RepositoryStars.objects.get(
            created_at=previous_date, repository=self
        )
        return self.stars - previous_stars.stars


class Contributor(TimeStampedModel):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="contributors",
        related_query_name="contributor",
    )
    contributions = models.PositiveIntegerField()

    def __str__(self):
        return f"<Contributor {self.profile.login} to {self.repository.full_name}>"


class RepositoryStars(models.Model):
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
    )
    created_at = models.DateField()
    stars = models.PositiveIntegerField()

    class Meta:
        unique_together = [["repository", "created_at"]]

    def __str__(self):
        return f"<RepositoryStars {self.repository.full_name} at {self.created_at}>"


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
