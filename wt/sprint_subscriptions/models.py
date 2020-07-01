from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from model_utils import Choices

from wt.plans.models import Plan
from wt.subscriptions.models import Subscription


class SprintSubscription(Subscription):
    """Represents a subscription with Sprint for a user and a single device"""
    STATUS = Choices(
        ('new', 'New'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    )
    ONE_KILOBYTE_PRICE = Decimal('0.0015')
    ONE_SECOND_PRICE = Decimal('0.0015')

    status = models.CharField(max_length=10, choices=STATUS, default=STATUS.new)
    sprint_id = models.CharField(max_length=16, null=True)

    class Meta:
        db_table = 'subscriptions_sprint'
