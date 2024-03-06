from django.db import models
from django.urls import reverse
from model_utils.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=5)

    def __str__(self):
        return f"<Category: {self.name}>"

    def get_absolute_url(self):
        return reverse("core:category-detail", args=[self.name])
