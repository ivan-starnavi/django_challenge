import datetime

from django.db import models

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription

from .base_models import UsageRecord, AggregatedUsageRecord, populate


class DataUsageRecord(UsageRecord):
    """Raw data usage record for a subscription"""
    kilobytes_used = models.IntegerField(null=False)

    USAGE_FIELD = 'kilobytes_used'


class VoiceUsageRecord(UsageRecord):
    """Raw voice usage record for a subscription"""
    seconds_used = models.IntegerField(null=False)

    USAGE_FIELD = 'seconds_used'


class AggregatedDataUsageRecord(AggregatedUsageRecord):
    """Aggregated data usage record for subscriptions by date"""
    kilobytes_used = models.IntegerField(default=0)

    BASE_MODEL = DataUsageRecord

    class Meta:
        db_table = 'agg_data_usage'

    @classmethod
    def populate(
            cls,
            date: datetime.date,
            att_subscription_id: int = None,
            sprint_subscription_id: int = None
    ) -> 'AggregatedDataUsageRecord':
        return populate(AggregatedDataUsageRecord, date, att_subscription_id, sprint_subscription_id)


class AggregatedVoiceUsageRecord(AggregatedUsageRecord):
    """Aggregated voice usage record for subscriptions by date"""
    seconds_used = models.IntegerField(default=0)

    BASE_MODEL = VoiceUsageRecord

    class Meta:
        db_table = 'agg_voice_usage'

    @classmethod
    def populate(
            cls,
            date: datetime.date,
            att_subscription_id: int = None,
            sprint_subscription_id: int = None
    ) -> 'AggregatedVoiceUsageRecord':
        return populate(AggregatedVoiceUsageRecord, date, att_subscription_id, sprint_subscription_id)
