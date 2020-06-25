from django.db.models import Sum, F, Q, Value, CharField
from django.db.models.functions import Coalesce

from rest_framework.response import Response
from rest_framework.views import APIView

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription

from .serializers import ExceedingATTSubscriptionSerializer


class StatsView(APIView):
    def get(self, request):
        limit = 1
        att_exceeded_subscriptions = ATTSubscription.objects\
            .annotate(agg_data_usage_exceeds=Coalesce(Sum('datausagerecord__price'), 0) - limit) \
            .annotate(agg_voice_usage_exceeds=Coalesce(Sum('voiceusagerecord__price'), 0) - limit) \
            .annotate(sub_type=Value('ATT', CharField())) \
            .filter(
                Q(agg_data_usage_exceeds__gt=0) | Q(agg_voice_usage_exceeds__gt=0)
            ) \
            .values('id', 'agg_data_usage_exceeds', 'agg_voice_usage_exceeds', 'sub_type')

        sprint_exceeded_subscriptions = SprintSubscription.objects\
            .annotate(agg_data_usage_exceeds=Coalesce(Sum('datausagerecord__price'), 0) - limit) \
            .annotate(agg_voice_usage_exceeds=Coalesce(Sum('voiceusagerecord__price'), 0) - limit) \
            .annotate(sub_type=Value('Sprint', CharField())) \
            .filter(
                Q(agg_data_usage_exceeds__gt=0) | Q(agg_voice_usage_exceeds__gt=0)
            ) \
            .values('id', 'agg_data_usage_exceeds', 'agg_voice_usage_exceeds', 'sub_type')

        q = att_exceeded_subscriptions.union(sprint_exceeded_subscriptions)

        # ser = ExceedingATTSubscriptionSerializer(att_exceeded_subscriptions, many=True)

        return Response(list(q))
