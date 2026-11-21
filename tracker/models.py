from django.conf import settings
from django.db import models


class AccountRecords(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    records = models.JSONField(default=list)
    revision = models.PositiveBigIntegerField(default=0)


class AuthAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
