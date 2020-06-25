from wt.sprint_subscriptions.models import SprintSubscription
from django.http import HttpResponse
from rest_framework import viewsets
from wt.sprint_subscriptions.serializers import SprintSubscriptionSerializer


class SprintSubscriptionViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.
    """
    queryset = SprintSubscription.objects.all()
    serializer_class = SprintSubscriptionSerializer
