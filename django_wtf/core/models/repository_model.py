from datetime import datetime, timedelta

import hanzidentifier
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.urls.base import reverse
from django.utils.text import Truncator
from model_utils.models import TimeStampedModel


class RepositoryType(models.TextChoices):
    PROJECT = ("project", "project")
    APP = ("app", "app")


# pylint: disable=too-few-public-methods
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
    objects = models.Manager()
    valid = RepositoryManager()
    github_id = models.PositiveIntegerField()
    owner = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        related_name="repositories",
        related_query_name="repository",
    )
    categories = models.ManyToManyField("core.Category", blank=True)
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

    def get_absolute_url(self):
        return reverse("core:repo-detail", args=[self.full_name])

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
