from rest_framework.serializers import Serializer, DecimalField, IntegerField, DateTimeField, ChoiceField, CharField, \
    SerializerMethodField


class CustomDecimalField(DecimalField):
    def __init__(self, *args, only_positive_values=True, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 10)
        kwargs.setdefault('coerce_to_string', True)
        super().__init__(*args, **kwargs)

        self.only_positive_values = only_positive_values

    def to_representation(self, value):
        if value <= 0 and self.only_positive_values:
            return None
        else:
            return super().to_representation(value)


class StatsExceedingRequestSerializer(Serializer):
    limit = CustomDecimalField()


class StatsExceedingResponseSerializer(Serializer):
    id = IntegerField()
    data_usage_exceeds = CustomDecimalField(source='agg_data_usage_exceeds')
    voice_usage_exceeds = CustomDecimalField(source='agg_voice_usage_exceeds')
    subscription_type = CharField()


class StatsUsageMetricsRequestSerializer(Serializer):
    from_date = DateTimeField(required=True)
    to_date = DateTimeField(required=True)
    usage_type = ChoiceField(choices=['data', 'voice'], required=True)


class StatusUsageMetricsResponseSerializer(Serializer):
    subscription_type = SerializerMethodField()
    subscription_id = IntegerField(source='id_value')
    usage = IntegerField(source='agg_usage')
    price = CustomDecimalField(only_positive_values=False, source='agg_price')

    def get_subscription_type(self, obj):
        subscription_type = obj.id_field
        if subscription_type == 'att_subscription_id':
            return 'ATT'
        elif subscription_type == 'sprint_subscription_id':
            return 'Sprint'
        else:
            raise RuntimeError(f'Unsupported subscription type: {subscription_type}')
