import datetime

from typing import Type

from django.db import models, transaction
from django.db.models import Subquery, F, Exists
from django.db.models.functions import Coalesce

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription
from wt.usage.managers import UsageQuerySet
from wt.usage.utils import chunks

POPULATE_BULK_CREATE_CHUNK_SIZE = 100


class UsageRecord(models.Model):
    """Abstract model for subscription usage"""
    att_subscription = models.ForeignKey(ATTSubscription, null=True, on_delete=models.PROTECT)
    sprint_subscription = models.ForeignKey(SprintSubscription, null=True, on_delete=models.PROTECT)
    price = models.DecimalField(decimal_places=2, max_digits=5, default=0)
    usage_date = models.DateTimeField(null=True)

    USAGE_FIELD: str = None

    objects = UsageQuerySet.as_manager()

    class Meta:
        abstract = True

    @classmethod
    def annotate_usage_by_subscription(cls, query: UsageQuerySet) -> UsageQuerySet:
        """Annotates queryset over UsageRecord child model with total usage and price by subscription. Returns annotated
            queryset with only fields: `id_field`, `id_value`, `att_subscription_id`, `sprint_subscription_id`"""
        # annotate with id fields
        query = query.annotate_id().filter_outer_id()
        # count usage by subscription
        query = query.values('id_field', 'id_value', 'att_subscription_id', 'sprint_subscription_id')
        query = query.annotate(
            agg_usage=Coalesce(models.Sum(cls.USAGE_FIELD), 0, output_field=models.IntegerField()),
            agg_price=Coalesce(models.Sum('price'), 0, output_field=models.IntegerField())
        )
        return query


class AggregatedUsageRecord(models.Model):
    """Abstract model for aggregated subscription usage by date"""
    att_subscription = models.ForeignKey(ATTSubscription, null=True, on_delete=models.PROTECT)
    sprint_subscription = models.ForeignKey(SprintSubscription, null=True, on_delete=models.PROTECT)
    price = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    usage_date = models.DateField()

    BASE_MODEL: Type[UsageRecord] = None

    objects = UsageQuerySet.as_manager()

    class Meta:
        abstract = True

    @classmethod
    def get_not_existing_aggregate_records(cls, date: datetime.date) -> UsageQuerySet:
        """Returns queryset (on BASE_MODEL) containing fields `att_subscription_id` and `sprint_subscription_id` that
            represent subscriptions without aggregated record for given date"""
        query = cls.BASE_MODEL.objects.filter(usage_date__date=date)
        query = query.values('att_subscription_id', 'sprint_subscription_id').distinct()
        query = query.annotate_id()

        subquery = cls.objects.annotate_id().filter_outer_id()
        subquery = subquery.filter(usage_date=date)

        query = query.annotate(agg_record_exists=Exists(subquery))
        query = query.filter(agg_record_exists=False)

        return query

    @classmethod
    @transaction.atomic()
    def populate(cls, date: datetime.date) -> None:
        """Populates aggregated usage model with raw records on given date and then deletes counted raw records"""
        # 1. create not existing aggregated records for given date for those subscription that have usage in given date
        agg_records_to_create = cls.get_not_existing_aggregate_records(date)
        for dicts in chunks(agg_records_to_create, POPULATE_BULK_CREATE_CHUNK_SIZE):
            objects = [
                cls(
                    pk=None,
                    att_subscription_id=d['att_subscription_id'],
                    sprint_subscription_id=d['sprint_subscription_id'],
                    usage_date=date
                )
                for d in dicts]
            cls.objects.bulk_create(objects)

        # 2. update aggregated records
        subquery = cls.BASE_MODEL.objects.filter(usage_date__date=date)
        subquery = cls.BASE_MODEL.annotate_usage_by_subscription(subquery)

        query = cls.objects.filter(usage_date=date).annotate_id()
        query = query.annotate(
            agg_usage=Subquery(subquery.values('agg_usage'), output_field=models.IntegerField()),
            agg_price=Subquery(subquery.values('agg_price'), output_field=models.DecimalField())
        )
        # counting only subscriptions with non-zero usage
        query = query.filter(agg_usage__gt=0)

        # update
        query.update(**{
            cls.BASE_MODEL.USAGE_FIELD: F(cls.BASE_MODEL.USAGE_FIELD) + F('agg_usage'),
            'price': F('price') + F('agg_price')
        })

        # 3. delete raw usage records that have been counted above
        cls.BASE_MODEL.objects.filter(usage_date__date=date).delete()
