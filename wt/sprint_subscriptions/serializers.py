from rest_framework import serializers
from wt.sprint_subscriptions.models import SprintSubscription


class SprintSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SprintSubscription
        fields = '__all__'
