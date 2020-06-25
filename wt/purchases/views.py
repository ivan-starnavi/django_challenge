from rest_framework import viewsets

from wt.purchases.models import Purchase
from wt.purchases.serializers import PurchaseSerializer


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
