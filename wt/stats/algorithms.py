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
    # TODO: write docs
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
    # TODO: write docs
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
    # TODO: write docs
    initial_query = initial_query.filter(usage_date__gte=from_date, usage_date__lte=to_date)

    initial_subquery = initial_query \
        .annotate(id_field=USAGE_ID_FIELD_ANNOTATION, id_value=USAGE_ID_VALUE_ANNOTATION) \
        .filter(id_field=OuterRef('id_field'))

    query = initial_query \
        .values('att_subscription_id', 'sprint_subscription_id') \
        .distinct() \
        .annotate(id_field=USAGE_ID_FIELD_ANNOTATION, id_value=USAGE_ID_VALUE_ANNOTATION)

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
