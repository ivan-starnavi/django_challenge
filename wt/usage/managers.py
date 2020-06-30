from django.db import models
from django.db.models.functions import Coalesce


USAGE_ID_FIELD_ANNOTATION = models.Case(
    models.When(att_subscription_id__isnull=False, then=models.Value('att_subscription_id')),
    default=models.Value('sprint_subscription_id'),
    output_field=models.CharField()
)

USAGE_ID_VALUE_ANNOTATION = Coalesce(
    'att_subscription_id',
    'sprint_subscription_id',
    output_field=models.IntegerField()
)


class UsageQuerySet(models.QuerySet):
    def annotate_id(self) -> 'UsageQuerySet':
        return self.annotate(
            id_field=USAGE_ID_FIELD_ANNOTATION,
            id_value=USAGE_ID_VALUE_ANNOTATION
        )

    def filter_outer_id(self) -> 'UsageQuerySet':
        return self.filter(
            id_field=models.OuterRef('id_field'),
            id_value=models.OuterRef('id_value')
        )
