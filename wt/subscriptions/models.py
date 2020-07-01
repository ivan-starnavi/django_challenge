from django.db import models
from django.contrib.auth.models import User

from wt.plans.models import Plan


class Subscription(models.Model):
    """Represents a subscription with AT&T for a user and a single device"""
    user = models.ForeignKey(User, on_delete=models.PROTECT)  # Owning user

    plan = models.ForeignKey(Plan, null=True, on_delete=models.PROTECT)

    device_id = models.CharField(max_length=20, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    phone_model = models.CharField(max_length=128, blank=True, default='')

    effective_date = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
