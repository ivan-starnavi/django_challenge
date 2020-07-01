from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from model_utils import Choices

from wt.plans.models import Plan
from wt.subscriptions.models import Subscription


class ATTSubscription(Subscription):
    ONE_KILOBYTE_PRICE = Decimal('0.001')
    ONE_SECOND_PRICE = Decimal('0.001')

    STATUS = Choices(
        ('new', 'New'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    )

    """Represents a subscription with AT&T for a user and a single device"""
    status = models.CharField(max_length=10, choices=STATUS, default=STATUS.new)
    network_type = models.CharField(max_length=5, blank=True, default='')

    class Meta:
        db_table = 'subscriptions_att'
