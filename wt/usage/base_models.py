import datetime

from typing import Optional, Dict, TypeVar, Type

from django.db import models, transaction
from django.db.models.functions import Coalesce

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription


class UsageRecord(models.Model):
    """Abstract model for subscription usage"""
    att_subscription = models.ForeignKey(ATTSubscription, null=True, on_delete=models.PROTECT)
    sprint_subscription = models.ForeignKey(SprintSubscription, null=True, on_delete=models.PROTECT)
    price = models.DecimalField(decimal_places=2, max_digits=5, default=0)
    usage_date = models.DateTimeField(null=True)

    USAGE_FIELD = None

    class Meta:
        abstract = True


class AggregatedUsageRecord(models.Model):
    """Abstract model for aggregated subscription usage by date"""
    att_subscription = models.ForeignKey(ATTSubscription, null=True, on_delete=models.PROTECT)
    sprint_subscription = models.ForeignKey(SprintSubscription, null=True, on_delete=models.PROTECT)
    price = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    usage_date = models.DateField()

    BASE_MODEL: UsageRecord = None

    class Meta:
        abstract = True


def construct_search(
        att_subscription_id: Optional[int] = None,
        sprint_subscription_id: Optional[int] = None
) -> Dict[str, int or bool]:
    result = {}

    if att_subscription_id is None:
        result['att_subscription_id__isnull'] = True
    else:
        result['att_subscription_id'] = att_subscription_id

    if sprint_subscription_id is None:
        result['sprint_subscription_id__isnull'] = True
    else:
        result['sprint_subscription_id'] = sprint_subscription_id

    return result


T = TypeVar('T', bound='AggregatedUsageRecord')


@transaction.atomic()
def populate(
        model: Type[T],
        date: datetime.date,
        att_subscription_id: int = None,
        sprint_subscription_id: int = None
) -> T:
    # TODO: replace with validator on model
    # TODO: write docs
    assert bool(att_subscription_id) ^ bool(sprint_subscription_id), 'You should pass only one of the ids'

    obj, _ = model.objects.get_or_create(
        att_subscription_id=att_subscription_id,
        sprint_subscription_id=sprint_subscription_id,
        defaults={
            'usage_date': date,
            'att_subscription_id': att_subscription_id,
            'sprint_subscription_id': sprint_subscription_id
        }
    )

    query = model.BASE_MODEL.objects.filter(
        usage_date__contains=date,
        **construct_search(att_subscription_id, sprint_subscription_id)
    )
    aggregation = query.aggregate(
        agg_usage=Coalesce(models.Sum(model.BASE_MODEL.USAGE_FIELD), 0, output_field=models.IntegerField()),
        agg_price=Coalesce(models.Sum('price'), 0, output_field=models.IntegerField())
    )

    setattr(obj, model.BASE_MODEL.USAGE_FIELD, getattr(obj, model.BASE_MODEL.USAGE_FIELD) + aggregation['agg_usage'])
    obj.price += aggregation['agg_price']
    obj.save()

    query.delete()

    return obj
