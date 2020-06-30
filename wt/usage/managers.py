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
    def annotate_id(self):
        return self.annotate(
            id_field=USAGE_ID_FIELD_ANNOTATION,
            id_value=USAGE_ID_VALUE_ANNOTATION
        )

    def filter_outer_id(self):
        return self.filter(
            id_field=models.OuterRef('id_field'),
            id_value=models.OuterRef('id_value')
        )

    def subquery_aggregate(self, need_usage=True, need_price=True):
        """Annotates queryset over UsageRecord child model with total usage and price by subscription. Returns annotated
            and filtered with outerref queryset with only fields: `id_field`, `id_value`, `att_subscription_id`,
            `sprint_subscription_id` and optional fields `agg_usage`, `agg_price`

            Args:
                need_usage (bool, Optional): need aggregated total usage in returned queryset (`agg_usage`)
                need_price (bool, Optional): need aggregated total price in returned queryset (`agg_price`)
        """

        if not hasattr(self.model, 'USAGE_FIELD'):
            raise RuntimeError('No `USAGE_FIELD` field for model of query')

        # annotate with id fields
        query = self.annotate_id().filter_outer_id()
        query = query.values('id_field', 'id_value', 'att_subscription_id', 'sprint_subscription_id')

        if need_usage:
            query = query.annotate(
                agg_usage=Coalesce(models.Sum(self.model.USAGE_FIELD), 0, output_field=models.IntegerField())
            )

        if need_price:
            query = query.annotate(
                agg_price=Coalesce(models.Sum('price'), 0, output_field=models.IntegerField())
            )

        return query
