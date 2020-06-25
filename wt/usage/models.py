from django.db import models

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription


class UsageRecord(models.Model):
    """Abstract model for subscription usage"""
    att_subscription_id = models.ForeignKey(ATTSubscription, null=True, on_delete=models.PROTECT)
    sprint_subscription_id = models.ForeignKey(SprintSubscription, null=True, on_delete=models.PROTECT)
    price = models.DecimalField(decimal_places=2, max_digits=5, default=0)
    usage_date = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class DataUsageRecord(UsageRecord):
    """Raw data usage record for a subscription"""
    kilobytes_used = models.IntegerField(null=False)


class VoiceUsageRecord(UsageRecord):
    """Raw voice usage record for a subscription"""
    seconds_used = models.IntegerField(null=False)
