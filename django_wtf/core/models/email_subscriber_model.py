from django.contrib.auth import get_user_model
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from model_utils.models import TimeStampedModel

User = get_user_model()


class EmailSubscriber(ExportModelOperationsMixin("email_subscriber"), TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscriber"
    )
