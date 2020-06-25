from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from model_utils import Choices

from wt.plans.models import Plan


class SprintSubscription(models.Model):
    """Represents a subscription with Sprint for a user and a single device"""
    STATUS = Choices(
        ('new', 'New'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    )
    ONE_KILOBYTE_PRICE = Decimal('0.0015')
    ONE_SECOND_PRICE = Decimal('0.0015')

    # Owning user
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    plan = models.ForeignKey(Plan, null=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS, default=STATUS.new)

    device_id = models.CharField(max_length=20, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    phone_model = models.CharField(max_length=128, blank=True, default='')

    sprint_id = models.CharField(max_length=16, null=True)

    effective_date = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    deleted = models.BooleanField(default=False)
