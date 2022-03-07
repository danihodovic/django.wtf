from django.db import models
from model_utils.models import TimeStampedModel


class UserType(models.TextChoices):
    USER = ("User", "User")
    ORGANIZATION = ("Organization", "Organization")
    BOT = ("Bot", "Bot")


class Profile(TimeStampedModel):
    github_id = models.PositiveIntegerField()
    login = models.CharField(max_length=100, unique=True)
    type = models.CharField(
        max_length=30, choices=UserType.choices, null=True, blank=True
    )
    avatar_url = models.URLField()


class Repository(TimeStampedModel):
    github_id = models.PositiveIntegerField()
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="repositories",
        related_query_name="repository",
    )
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100, unique=True)
    forks = models.PositiveIntegerField()
    open_issues = models.PositiveIntegerField()
    watchers = models.PositiveIntegerField()
    stars = models.PositiveIntegerField()


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


class RepositoryStars(models.Model):
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
    )
    created_at = models.DateField()
    stars = models.PositiveIntegerField()


class ProfileFollowers(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="followers",
        related_query_name="follower",
    )
    created_at = models.DateField()
    followers = models.PositiveIntegerField()

    class Meta:
        unique_together = (
            "profile",
            "created_at",
        )
