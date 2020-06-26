from rest_framework.serializers import Serializer, DecimalField, IntegerField


class ExceedingDecimalField(DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 10)
        kwargs.setdefault('coerce_to_string', True)
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if value <= 0:
            return None
        else:
            return super().to_representation(value)


class StatsExceedingRequestSerializer(Serializer):
    limit = ExceedingDecimalField()


class StatsExceedingResponseSerializer(Serializer):
    id = IntegerField()
    data_usage_exceeds = ExceedingDecimalField(source='agg_data_usage_exceeds')
    voice_usage_exceeds = ExceedingDecimalField(source='agg_voice_usage_exceeds')

    class Meta:
        fields = ['id', 'data_usage_exceeds', 'voice_usage_exceeds', 'subscription_type']
