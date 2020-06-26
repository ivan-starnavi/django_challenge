from rest_framework.response import Response
from rest_framework.views import APIView

from wt.att_subscriptions.models import ATTSubscription
from wt.sprint_subscriptions.models import SprintSubscription

from .algorithms import get_exceeding_subscriptions
from .serializers import StatsExceedingRequestSerializer, StatsExceedingResponseSerializer


class StatsExceedingView(APIView):
    def get(self, request):
        query_serializer = StatsExceedingRequestSerializer(data=request.query_params)
        query_serializer.is_valid(True)
        limit = query_serializer.validated_data['limit']

        att_exceeded_subscriptions = get_exceeding_subscriptions(
            ATTSubscription.objects.all(),
            'ATT',
            limit
        )
        sprint_exceeded_subscriptions = get_exceeding_subscriptions(
            SprintSubscription.objects.all(),
            'Sprint',
            limit
        )

        q = att_exceeded_subscriptions.union(sprint_exceeded_subscriptions)

        data = StatsExceedingResponseSerializer(q, many=True).data

        return Response(data)
