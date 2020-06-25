from rest_framework.serializers import ModelSerializer, ListSerializer

from wt.att_subscriptions.models import ATTSubscription


class ExceedingATTSubscriptionSerializer(ModelSerializer):
    class Meta:
        model = ATTSubscription
        fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['exceeds'] = []

        if instance['agg_data_usage_exceeds'] > 0:
            data['exceeds'].append({
                'type': 'data',
                'over_limit': instance.agg_data_usage_exceeds
            })

        if instance['agg_voice_usage_exceeds'] > 0:
            data['exceeds'].append({
                'type': 'voice',
                'over_limit': instance.agg_voice_usage_exceeds
            })

        return data
