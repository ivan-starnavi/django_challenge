import datetime

from django.db.models import Sum, Q, Value, CharField, QuerySet, OuterRef, Subquery, Case, When, DecimalField, \
    IntegerField
from django.db.models.functions import Coalesce

from wt.usage.models import DataUsageRecord, VoiceUsageRecord

USAGE_ID_FIELD_ANNOTATION = Case(
    When(att_subscription_id__isnull=False, then=Value('att_subscription_id')),
    default=Value('sprint_subscription_id'),
    output_field=CharField()
)
USAGE_ID_VALUE_ANNOTATION = Coalesce(
    'att_subscription_id',
    'sprint_subscription_id',
    output_field=IntegerField()
)


def get_usage_aggregated_query(
        initial_query: QuerySet,
        query_id_field: str,
        outer_query_id_field: str,
        aggregated_field: str
) -> QuerySet:
    """This function takes initial queryset on child model of wt.usage.base_models.UsageRecord and using passed field
        names returns modified initial queryset that aggregates usage over certain subscription (using Coalesce(Sum, 0))

    Args:
        initial_query (QuerySet): initial queryset on child model of wt.usage.base_models.UsageRecord
        query_id_field (str): subscription id field name on initial_query
        outer_query_id_field (str): outer reference subscription id field name (e.g. att_subscription_id)
        aggregated_field (str): field name on initial_query to aggregate sum

    Returns:
        Queryset: modified initial queryset with only field named `sum_{aggregated_field}` that contains total usage
            over given subscription
    """
    query = initial_query.filter(**{query_id_field: OuterRef(outer_query_id_field)})
    query = query.values(query_id_field)
    query = query.annotate(**{'sum_' + aggregated_field: Coalesce(Sum(aggregated_field), 0)})
    query = query.values('sum_' + aggregated_field)
    return query


def get_exceeding_subscriptions(
        initial_query: QuerySet,
        subscription_type: str,
        subscription_id_field: str,
        limit: float
) -> QuerySet:
    """This function takes initial queryset on subscription model (ATT or Spring) and annotates it with new field
        (`subscription_type`) containing information of subscription type (based on given `subscription_type`) and
        fields (`agg_data_usage_exceeds`, `agg_voice_usage_exceeds`) containing information on exceeding given `limit`
        for all types of usage

    Args:
        initial_query (QuerySet): initial queryset on child model of wt.usage.base_models.UsageRecord
        subscription_type (str): subscription id field name on initial_query
        subscription_id_field (str): outer reference subscription id field name (e.g. att_subscription_id)
        limit (float): field name on initial_query to aggregate sum

    Returns:
        Queryset: annotated initial queryset
    """
    data_usage_subquery = get_usage_aggregated_query(
        DataUsageRecord.objects.all(),
        subscription_id_field,
        'id',
        'price'
    )
    voice_usage_subquery = get_usage_aggregated_query(
        VoiceUsageRecord.objects.all(),
        subscription_id_field,
        'id',
        'price'
    )

    query = initial_query
    query = query.annotate(
        agg_data_usage_exceeds=Subquery(data_usage_subquery) - limit,
        agg_voice_usage_exceeds=Subquery(voice_usage_subquery) - limit,
        subscription_type=Value(subscription_type, CharField())
    )
    query = query.filter(Q(agg_data_usage_exceeds__gt=0) | Q(agg_voice_usage_exceeds__gt=0))
    return query


def get_usage_metrics(
        initial_query: QuerySet,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
) -> QuerySet:
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
    initial_query = initial_query.filter(usage_date__gte=from_date, usage_date__lte=to_date)

    initial_subquery = initial_query.annotate(
        id_field=USAGE_ID_FIELD_ANNOTATION,
        id_value=USAGE_ID_VALUE_ANNOTATION
    )
    initial_subquery = initial_subquery.filter(id_field=OuterRef('id_field'))

    query = initial_query.values('att_subscription_id', 'sprint_subscription_id')
    query = query.distinct()
    query = query.annotate(
        id_field=USAGE_ID_FIELD_ANNOTATION,
        id_value=USAGE_ID_VALUE_ANNOTATION
    )

    price_aggregated_query = get_usage_aggregated_query(
        initial_subquery, 'id_value', 'id_value', 'price'
    )
    usage_aggregated_query = get_usage_aggregated_query(
        initial_subquery, 'id_value', 'id_value', initial_query.model.USAGE_FIELD
    )

    query = query.annotate(
        agg_price=Subquery(price_aggregated_query, output_field=DecimalField()),
        agg_usage=Subquery(usage_aggregated_query, output_field=IntegerField()),
    )
    # filter subscriptions that have usage within given period
    query = query.filter(agg_usage__gt=0)
    return query
