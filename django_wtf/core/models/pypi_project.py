from django.db import models
from model_utils.models import TimeStampedModel


class PypiProject(TimeStampedModel):
    repository = models.OneToOneField("core.Repository", on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    author_email = models.EmailField()
    homepage = models.URLField()
    summary = models.CharField(max_length=300)
    version = models.CharField(max_length=12)
    requires_python = models.CharField(max_length=20, null=True, blank=True)
    license = models.CharField(max_length=70)

    def __str__(self):
        return f"<PypiProject: {self.repository.full_name}>"
