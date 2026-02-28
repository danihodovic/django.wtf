from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin
from model_utils.models import TimeStampedModel


class Category(ExportModelOperationsMixin("category"), TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=5)

    def __str__(self):
        return f"<Category: {self.name}>"

    def get_absolute_url(self):
        return reverse("core:category-detail", args=[self.name])
