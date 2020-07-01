from django.db import models

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription

from .base_models import UsageRecord, AggregatedUsageRecord


class DataUsageRecord(UsageRecord):
    """Raw data usage record for a subscription"""
    kilobytes_used = models.IntegerField(null=False)

    USAGE_FIELD = 'kilobytes_used'

    class Meta:
        db_table = 'usages_data'


class VoiceUsageRecord(UsageRecord):
    """Raw voice usage record for a subscription"""
    seconds_used = models.IntegerField(null=False)

    USAGE_FIELD = 'seconds_used'

    class Meta:
        db_table = 'usages_voice'


class AggregatedDataUsageRecord(AggregatedUsageRecord):
    """Aggregated data usage record for subscriptions by date"""
    kilobytes_used = models.IntegerField(default=0)

    BASE_MODEL = DataUsageRecord

    class Meta:
        db_table = 'usages_agg_data'


class AggregatedVoiceUsageRecord(AggregatedUsageRecord):
    """Aggregated voice usage record for subscriptions by date"""
    seconds_used = models.IntegerField(default=0)

    BASE_MODEL = VoiceUsageRecord

    class Meta:
        db_table = 'usages_agg_voice'
