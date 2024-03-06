from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel

User = get_user_model()


class EmailSubscriber(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscriber"
    )
