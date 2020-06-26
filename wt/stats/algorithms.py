from django.db.models import Sum, Q, Value, CharField, QuerySet
from django.db.models.functions import Coalesce


def get_exceeding_subscriptions(initial_query: QuerySet, subscription_type: str, limit: float) -> QuerySet:
    query = initial_query.annotate(agg_data_usage_exceeds=Coalesce(Sum('datausagerecord__price'), 0) - limit)
    query = query.annotate(agg_voice_usage_exceeds=Coalesce(Sum('voiceusagerecord__price'), 0) - limit)
    query = query.filter(Q(agg_data_usage_exceeds__gt=0) | Q(agg_voice_usage_exceeds__gt=0))
    query = query.annotate(subscription_type=Value(subscription_type, CharField()))
    query = query.values('id', 'agg_data_usage_exceeds', 'agg_voice_usage_exceeds', 'subscription_type')
    return query
