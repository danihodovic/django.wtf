from django.db import models


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
