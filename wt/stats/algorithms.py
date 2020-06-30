import datetime

from django.db import models

from wt.usage.base_models import UsageRecord
from wt.usage.managers import UsageQuerySet
from wt.usage.models import DataUsageRecord, VoiceUsageRecord


def get_exceeding_subscriptions(initial_query: models.QuerySet, limit: float) -> models.QuerySet:
    """This function takes initial queryset on subscription model (ATT or Spring) and annotates it with new field
        (`subscription_type`) contains class name of subscription model and fields (`agg_data_usage_exceeds`,
        `agg_voice_usage_exceeds`) containing information on exceeding given `limit` for all types of usage

    Args:
        initial_query (QuerySet): initial queryset on child model of wt.usage.base_models.UsageRecord
        limit (float): field name on initial_query to aggregate sum

    Returns:
        Queryset: annotated initial queryset
    """
    query = initial_query
    query = query.annotate(
        id_value=models.F('id'),
        id_field=models.Value(UsageRecord.get_related_field_name_by_model(query.model), output_field=models.CharField())
    )

    subquery_data = DataUsageRecord.objects.subquery_aggregate(need_usage=False).values('agg_price')
    subquery_voice = VoiceUsageRecord.objects.subquery_aggregate(need_usage=False).values('agg_price')

    query = query.annotate(
        agg_data_usage_exceeds=models.Subquery(subquery_data, output_field=models.DecimalField()) - limit,
        agg_voice_usage_exceeds=models.Subquery(subquery_voice, output_field=models.DecimalField()) - limit,
        subscription_type=models.Value(query.model.__name__, models.CharField())
    )
    query = query.filter(models.Q(agg_data_usage_exceeds__gt=0) | models.Q(agg_voice_usage_exceeds__gt=0))
    return query


def get_usage_metrics(
        initial_query: UsageQuerySet,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
) -> models.QuerySet:
    """This function takes initial queryset on child model of wt.usage.base_models.UsageRecord and annotates it with:
        *   subscription identifier (`id_field`, `id_value` annotated fields),
        *   total usage and price (`agg_usage`, `agg_price`) within given period (`from_date`, `to_date`)

    Args:
        initial_query (QuerySet): initial queryset on child model of wt.usage.base_models.UsageRecord
        from_date (datetime.datetime): start date of period
        to_date (datetime.datetime): end date of period

    Returns:
        Queryset: annotated initial queryset
    """
    query = initial_query
    query = query.filter(usage_date__gte=from_date, usage_date__lte=to_date)

    subquery_price = query.subquery_aggregate(need_usage=False).values('agg_price')
    subquery_usage = query.subquery_aggregate(need_price=False).values('agg_usage')

    query = query.annotate_id()
    query = query.values('id_field', 'id_value')
    query = query.distinct()
    query = query.annotate(
        agg_price=models.Subquery(subquery_price, output_field=models.DecimalField()),
        agg_usage=models.Subquery(subquery_usage, output_field=models.IntegerField()),
    )
    # filter subscriptions that have usage within given period
    query = query.filter(agg_usage__gt=0)
    return query
