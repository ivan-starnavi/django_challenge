from rest_framework.response import Response
from rest_framework.views import APIView

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription
from wt.usage.models import VoiceUsageRecord, DataUsageRecord

from .algorithms import get_exceeding_subscriptions, get_usage_metrics
from .serializers import StatsExceedingRequestSerializer, StatsExceedingResponseSerializer
from .serializers import StatsUsageMetricsRequestSerializer, StatusUsageMetricsResponseSerializer


class StatsExceedingView(APIView):
    def post(self, request):
        query_serializer = StatsExceedingRequestSerializer(data=request.data)
        query_serializer.is_valid(True)
        limit = query_serializer.validated_data['limit']

        att_exceeded_subscriptions = get_exceeding_subscriptions(
            ATTSubscription.objects.all(),
            'ATT',
            'att_subscription_id_id',
            limit
        )
        sprint_exceeded_subscriptions = get_exceeding_subscriptions(
            SprintSubscription.objects.all(),
            'Sprint',
            'sprint_subscription_id_id',
            limit
        )

        query = att_exceeded_subscriptions.union(sprint_exceeded_subscriptions)
        data = StatsExceedingResponseSerializer(query, many=True).data
        return Response(data)


class StatsUsageMetricsView(APIView):
    def post(self, request):
        request_serializer = StatsUsageMetricsRequestSerializer(data=request.data)
        request_serializer.is_valid(True)
        request_params = request_serializer.validated_data

        if request_params['usage_type'] == 'data':
            initial_query = DataUsageRecord.objects.all()
        else:
            initial_query = VoiceUsageRecord.objects.all()

        query = get_usage_metrics(initial_query, request_params['from_date'], request_params['to_date'])
        data = StatusUsageMetricsResponseSerializer(query, many=True).data
        return Response(data)
