# pylint: disable=too-few-public-methods
import logging
from datetime import datetime, timedelta

import hanzidentifier
from cacheops import cached_as
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.urls.base import reverse
from django.utils.text import Truncator
from model_utils.models import TimeStampedModel

User = get_user_model()


class UserType(models.TextChoices):
    USER = ("User", "User")
    ORGANIZATION = ("Organization", "Organization")
    BOT = ("Bot", "Bot")


class RepositoryType(models.TextChoices):
    PROJECT = ("project", "project")
    APP = ("app", "app")


class ProfileContributesToValidProjectsManager(models.Manager):
    def get_queryset(self):
        # If it has a category it's been manually categorized
        valid_repos = Repository.valid.all()
        return (
            super()
            .get_queryset()
            .filter(contributor__repository__in=valid_repos)
            .distinct()
        )


class Profile(TimeStampedModel):
    objects = models.Manager()  # type: ignore
    contributes_to_valid_repos = ProfileContributesToValidProjectsManager()  # type: ignore
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


class Category(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=5)

    def __str__(self):
        return f"<Category: {self.name}>"

    def get_absolute_url(self):
        return reverse("core:category-detail", args=[self.name])


class RepositoryManager(models.Manager):
    def get_queryset(self):
        # If it has a category it's been manually categorized
        return (
            super()
            .get_queryset()
            .filter(Q(categories__isnull=False) | Q(type=RepositoryType.APP))
            .distinct()
        )


class Repository(TimeStampedModel):
    objects = models.Manager()  # type: ignore
    valid = RepositoryManager()  # type: ignore
    github_id = models.PositiveIntegerField()
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="repositories",
        related_query_name="repository",
    )
    categories = models.ManyToManyField(Category, blank=True)
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
    readme_html = models.TextField(null=True)

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
        try:
            previous_stars = RepositoryStars.objects.get(
                created_at=previous_date, repository=self
            )
        except ObjectDoesNotExist:
            return 0
        return self.stars - previous_stars.stars

    @property
    def truncated_description(self):
        length = 90
        try:
            # Chinese letters are much longer than latin
            if hanzidentifier.has_chinese(self.description):
                length = 60
        except TypeError:
            pass
        return Truncator(self.description or "").chars(length)


class PypiProject(TimeStampedModel):
    repository = models.OneToOneField(Repository, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    author_email = models.EmailField()
    homepage = models.URLField()
    summary = models.CharField(max_length=300)
    version = models.CharField(max_length=12)
    requires_python = models.CharField(max_length=20, null=True, blank=True)
    license = models.CharField(max_length=70)

    def __str__(self):
        return f"<PypiProject: {self.repository.full_name}>"


class PypiRelease(models.Model):
    project = models.ForeignKey(
        PypiProject,
        on_delete=models.CASCADE,
    )
    version = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField()

    class Meta:
        unique_together = [["project", "version"]]

    def __str__(self):
        version = self.version
        return f"<PypiRelease: {self.project.repository.full_name} {version=}>"

    def pypi_release_url(self):
        return (
            f"https://pypi.org/project/{self.project.repository.name}/{self.version}/"
        )


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


class SocialNewsType(models.TextChoices):
    REDDIT = ("Reddit", "Reddit")
    HACKER_NEWS = ("Hacker News", "Hacker News")


class SocialNews(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField()
    type = models.CharField(
        max_length=30, choices=SocialNewsType.choices, null=True, blank=True
    )
    upvotes = models.IntegerField()
    created_at = models.DateTimeField()

    def __str__(self):
        type = self.type  # pylint: disable=redefined-builtin
        title = (self.title[:25] + "..") if len(self.title) > 25 else self.title
        return f"<SocialNews {type=} {title=}>"


class EmailSubscriber(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscriber"
    )
