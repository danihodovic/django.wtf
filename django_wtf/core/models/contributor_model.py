from django.db import models
from model_utils.models import TimeStampedModel


class Contributor(TimeStampedModel):
    profile = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
    )
    repository = models.ForeignKey(
        "core.Repository",
        on_delete=models.CASCADE,
        related_name="contributors",
        related_query_name="contributor",
    )
    contributions = models.PositiveIntegerField()

    def __str__(self):
        return f"<Contributor {self.profile.login} to {self.repository.full_name}>"
